"""MLflow storage, cohort-scoped selection and artifact-bound serving evidence."""

import json
import math
import os
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import mlflow.sklearn
import pandas as pd
from mlflow.tracking import MlflowClient

from ...config import Config
from .features import FEATURE_COLUMNS, RAW_COLUMNS, TripFeatureTransformer
from .provenance import VALIDATION_METRICS, valid_manifest, valid_metrics

MODEL_ARTIFACT_PATH = "model"
REQUIRED_VALIDATION_METRICS = VALIDATION_METRICS
_ARTIFACT_LOCK = threading.RLock()


class ModelUnavailable(RuntimeError):
    """No attributable inference result can be returned for this request."""


@dataclass(frozen=True)
class LoadedModel:
    model: object
    info: dict


class MLflowAdapter:
    def __init__(self, tracking_uri=None, experiment_name=None, *, cohort_id=None, run_id=None):
        with _ARTIFACT_LOCK:
            config = Config()
            self.tracking_uri = tracking_uri or config.mlflow_tracking_uri
            self.experiment_name = experiment_name or config.mlflow_experiment_name
            self.cohort_id = cohort_id if cohort_id is not None else config.model_cohort_id
            self.run_id = run_id if run_id is not None else config.model_run_id
        # Metadata operations use the explicit client. MLflow 3.1 artifact APIs still
        # consult process-global tracking state internally; guard and restore that state.
        self.client = MlflowClient(tracking_uri=self.tracking_uri)

    @contextmanager
    def _artifact_context(self):
        # No await inside this scope. All artifact operations in this application use
        # the same lock, including failure paths, and do not leave a global URI behind.
        with _ARTIFACT_LOCK:
            previous = mlflow.get_tracking_uri()
            previous_environment = os.environ.get("MLFLOW_TRACKING_URI")
            mlflow.set_tracking_uri(self.tracking_uri)
            try:
                yield
            finally:
                mlflow.set_tracking_uri(previous)
                # MLflow also writes this environment variable. Preserve independently
                # supplied application config even if its old global URI differed.
                if previous_environment is None:
                    os.environ.pop("MLFLOW_TRACKING_URI", None)
                else:
                    os.environ["MLFLOW_TRACKING_URI"] = previous_environment

    def _experiment(self, create=False):
        experiment = self.client.get_experiment_by_name(self.experiment_name)
        if experiment is None and create:
            experiment_id = self.client.create_experiment(self.experiment_name)
            return self.client.get_experiment(experiment_id)
        return experiment

    @property
    def experiment_id(self):
        experiment = self._experiment()
        return experiment.experiment_id if experiment else None

    async def save_model(
        self, model, model_name, metrics, features, hyperparams=None, *, provenance
    ):
        if not valid_metrics(metrics):
            raise ValueError("Missing or nonfinite measured validation metrics")
        if not valid_manifest(provenance):
            raise ValueError("A valid dataset/evaluation provenance manifest is required")
        expected = {
            "provenance": provenance,
            "metrics": metrics,
            "model_type": model_name,
            "features": features,
            "raw_columns": RAW_COLUMNS,
        }
        if getattr(model, "lifecycle_metadata_", None) != expected:
            raise ValueError("Artifact metadata differs from the supplied training evidence")
        if features != FEATURE_COLUMNS or not isinstance(
            model.named_steps.get("features"), TripFeatureTransformer
        ):
            raise ValueError("Artifact must include the supported raw-trip transformer")
        run = self.client.create_run(
            self._experiment(create=True).experiment_id,
            tags={"mlflow.runName": f"{model_name}_experiment"},
        )
        run_id = run.info.run_id
        try:
            params = {
                "model_type": model_name,
                "features": json.dumps(features),
                "provenance": json.dumps(provenance, sort_keys=True),
                "metrics_provenance": "measured_validation_split",
                "artifact_path": MODEL_ARTIFACT_PATH,
                "synthetic_data": str(provenance["data_kind"] == "synthetic").lower(),
                "cohort_id": provenance["cohort_id"],
                **(hyperparams or {}),
            }
            for key, value in params.items():
                self.client.log_param(run_id, key, value)
            for key, value in metrics.items():
                if not math.isfinite(float(value)):
                    raise ValueError("All recorded metrics must be finite")
                self.client.log_metric(run_id, key, float(value))
            with tempfile.TemporaryDirectory() as directory:
                model_path = Path(directory) / MODEL_ARTIFACT_PATH
                mlflow.sklearn.save_model(model, model_path)
                with self._artifact_context():
                    self.client.log_artifacts(
                        run_id, str(model_path), artifact_path=MODEL_ARTIFACT_PATH
                    )
            self.client.set_terminated(run_id, "FINISHED")
            return run_id
        except Exception:
            self.client.set_terminated(run_id, "FAILED")
            raise

    def _model_runs(self):
        experiment = self._experiment()
        if experiment is None:
            return []
        runs, token = [], None
        while True:
            page = self.client.search_runs(
                [experiment.experiment_id],
                filter_string="attributes.status = 'FINISHED'",
                order_by=["attributes.start_time DESC", "attributes.run_id ASC"],
                max_results=100,
                page_token=token,
            )
            for run in page:
                with self._artifact_context():
                    artifacts = self.client.list_artifacts(run.info.run_id)
                if any(item.path == MODEL_ARTIFACT_PATH and item.is_dir for item in artifacts):
                    runs.append(run)
            token = page.token
            if not token:
                return runs

    @staticmethod
    def _provenance(run):
        try:
            value = json.loads(run.data.params.get("provenance", "null"))
            return value if isinstance(value, dict) and valid_manifest(value) else None
        except (TypeError, ValueError):
            return None

    @classmethod
    def _eligible(cls, run):
        provenance = cls._provenance(run)
        return bool(
            provenance
            and valid_metrics(run.data.metrics)
            and run.data.params.get("metrics_provenance") == "measured_validation_split"
            and run.data.params.get("cohort_id") == provenance["cohort_id"]
            and run.data.params.get("synthetic_data")
            == str(provenance["data_kind"] == "synthetic").lower()
        )

    @staticmethod
    def _run_order(run):
        return (run.data.metrics["rmse"], -run.info.start_time, run.info.run_id)

    def _checked_run(self, run_id):
        run = self.client.get_run(run_id)
        if run.info.experiment_id != self.experiment_id or run.info.status != "FINISHED":
            raise ModelUnavailable("Requested run is not finished in the configured experiment")
        return run

    def _best_model_run(self):
        if self.run_id:
            run = self._checked_run(self.run_id)
            if not self._eligible(run):
                raise ModelUnavailable(
                    "Pinned run lacks verified lifecycle evidence; retrain before serving"
                )
            if self.cohort_id and self._provenance(run)["cohort_id"] != self.cohort_id:
                raise ModelUnavailable("Pinned run is outside the configured evaluation cohort")
            return run
        runs = [run for run in self._model_runs() if self._eligible(run)]
        if self.cohort_id:
            runs = [run for run in runs if self._provenance(run)["cohort_id"] == self.cohort_id]
        cohorts = {self._provenance(run)["cohort_id"] for run in runs}
        if len(cohorts) > 1:
            raise ModelUnavailable(
                "Multiple evaluation cohorts exist; set TAXI_MODEL_COHORT_ID or TAXI_MODEL_RUN_ID"
            )
        return min(runs, key=self._run_order) if runs else None

    def _info(self, run):
        eligible = self._eligible(run)
        try:
            features = json.loads(run.data.params.get("features", "[]"))
        except (TypeError, ValueError):
            features = []
        return {
            "run_id": run.info.run_id,
            "artifact_uri": f"runs:/{run.info.run_id}/{MODEL_ARTIFACT_PATH}",
            "model_type": run.data.params.get("model_type", "NOT_AVAILABLE"),
            "metrics_status": "MEASURED" if eligible else "NOT_AVAILABLE",
            "metrics_provenance": "measured_validation_split" if eligible else "NOT_AVAILABLE",
            **{
                key: float(run.data.metrics[key]) if eligible else None
                for key in VALIDATION_METRICS
            },
            "features": features if isinstance(features, list) else [],
            "provenance": self._provenance(run),
            "selection_status": "ELIGIBLE" if eligible else "LEGACY_OR_INVALID",
            "created_at": datetime.fromtimestamp(
                run.info.start_time / 1000, tz=timezone.utc
            ).isoformat(),
        }

    async def get_model_info(self, run_id=None):
        # Explicit historical inspection is safe even when a legacy run cannot serve.
        run = (
            self._checked_run(run_id or self.run_id)
            if (run_id or self.run_id)
            else self._best_model_run()
        )
        return self._info(run) if run else None

    async def load_selected_model(self, run_id=None):
        try:
            run = self._checked_run(run_id) if run_id else self._best_model_run()
            if run is None or not self._eligible(run):
                raise ModelUnavailable("No model with verified lifecycle evidence is available")
            if self.run_id and run.info.run_id != self.run_id:
                raise ModelUnavailable("Requested artifact differs from the configured run pin")
            if self.cohort_id and self._provenance(run)["cohort_id"] != self.cohort_id:
                raise ModelUnavailable(
                    "Requested artifact is outside the configured evaluation cohort"
                )
            with tempfile.TemporaryDirectory() as directory:
                with self._artifact_context():
                    path = self.client.download_artifacts(
                        run.info.run_id, MODEL_ARTIFACT_PATH, directory
                    )
                model = mlflow.sklearn.load_model(path)
            info = self._info(run)
            expected = {
                "provenance": info["provenance"],
                "metrics": dict(run.data.metrics),
                "model_type": info["model_type"],
                "features": info["features"],
                "raw_columns": RAW_COLUMNS,
            }
            if getattr(model, "lifecycle_metadata_", None) != expected:
                raise ModelUnavailable("Artifact and run metadata do not agree")
            if not isinstance(model.named_steps.get("features"), TripFeatureTransformer):
                raise ModelUnavailable(
                    "Artifact does not contain the supported raw-trip transformer"
                )
            return LoadedModel(model=model, info=info)
        except ModelUnavailable:
            raise
        except Exception as exc:
            raise ModelUnavailable("The selected model artifact could not be loaded") from exc

    async def load_best_model(self):
        return (await self.load_selected_model()).model

    async def compare_models(self, limit=10):
        # Different cohorts remain visible but are never ranked against each other.
        records = [self._info(run) for run in self._model_runs()]
        return pd.DataFrame(records[:limit])
