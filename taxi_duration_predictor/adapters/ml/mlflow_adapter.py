"""
MLflow Adapter - Taxi Duration Predictor
Implementación de MLflow para tracking y model registry
"""

import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.entities import Run
from mlflow.tracking import MlflowClient

try:
    from ...domain.ports import ModelRepository, ExperimentTracker
    from ...domain.entities import Prediction, TripFeatures
except ImportError:
    # Fallback for when running outside package context
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.append(str(project_root))
    from taxi_duration_predictor.domain.ports import ModelRepository, ExperimentTracker
    from taxi_duration_predictor.domain.entities import Prediction, TripFeatures

logger = logging.getLogger(__name__)

REQUIRED_VALIDATION_METRICS = ("rmse", "mae", "r2_score")
MODEL_ARTIFACT_PATH = "model"


class MLflowAdapter(ModelRepository, ExperimentTracker):
    """Adapter para MLflow - maneja tracking y model registry"""

    def __init__(
        self,
        tracking_uri: str = "sqlite:///data/mlflow.db",
        experiment_name: str = "taxi_duration_prediction",
    ):
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self._setup_mlflow()
        self.client = MlflowClient(tracking_uri=self.tracking_uri)

    def _setup_mlflow(self) -> None:
        """Configura MLflow tracking"""
        mlflow.set_tracking_uri(self.tracking_uri)
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            self.experiment_id = mlflow.create_experiment(self.experiment_name)
        else:
            self.experiment_id = experiment.experiment_id

    async def save_model(
        self,
        model: Any,
        model_name: str,
        metrics: Dict[str, float],
        features: List[str],
        hyperparams: Dict[str, Any] = None,
    ) -> str:
        """Save one complete inference artifact with measured validation evidence."""
        missing = set(REQUIRED_VALIDATION_METRICS) - metrics.keys()
        if missing:
            raise ValueError(f"Missing measured validation metrics: {sorted(missing)}")

        mlflow.set_tracking_uri(self.tracking_uri)
        with mlflow.start_run(
            experiment_id=self.experiment_id,
            run_name=f"{model_name}_experiment",
        ) as run:
            mlflow.log_param("model_type", model_name)
            mlflow.log_param("features", json.dumps(features))
            mlflow.log_param("feature_count", len(features))
            mlflow.log_param("metrics_provenance", "measured_validation_split")
            mlflow.log_param("artifact_path", MODEL_ARTIFACT_PATH)

            if hyperparams:
                mlflow.log_params(hyperparams)

            mlflow.log_metrics({key: float(value) for key, value in metrics.items()})
            with tempfile.TemporaryDirectory() as temporary_directory:
                model_path = Path(temporary_directory) / MODEL_ARTIFACT_PATH
                mlflow.sklearn.save_model(model, model_path)
                mlflow.log_artifacts(model_path, artifact_path=MODEL_ARTIFACT_PATH)

            logger.info(f"Modelo {model_name} guardado con run_id: {run.info.run_id}")
            return run.info.run_id

    def _model_runs(self) -> list[Run]:
        runs = self.client.search_runs(
            experiment_ids=[self.experiment_id],
            filter_string="attributes.status = 'FINISHED'",
            max_results=100,
        )
        model_runs = []
        for run in runs:
            try:
                artifacts = self.client.list_artifacts(run.info.run_id)
            except Exception as exc:
                logger.warning(
                    "Could not inspect artifacts for run %s: %s",
                    run.info.run_id,
                    exc,
                )
                continue
            if any(
                item.path == MODEL_ARTIFACT_PATH and item.is_dir for item in artifacts
            ):
                model_runs.append(run)
        return model_runs

    @staticmethod
    def _run_order(run: Run) -> tuple[bool, float, int]:
        has_all_metrics = all(
            key in run.data.metrics for key in REQUIRED_VALIDATION_METRICS
        )
        rmse = run.data.metrics.get("rmse")
        return (
            not has_all_metrics,
            float("inf") if rmse is None else rmse,
            -run.info.start_time,
        )

    def _best_model_run(self) -> Optional[Run]:
        runs = self._model_runs()
        return min(runs, key=self._run_order) if runs else None

    async def load_best_model(self) -> Optional[Any]:
        """Load the complete model/preprocessing artifact from the selected run."""
        run = self._best_model_run()
        if run is None:
            return None
        mlflow.set_tracking_uri(self.tracking_uri)
        return mlflow.sklearn.load_model(
            f"runs:/{run.info.run_id}/{MODEL_ARTIFACT_PATH}"
        )

    async def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Return only metadata and metrics stored with the selected model artifact."""
        run = self._best_model_run()
        if run is None:
            return None

        stored_metrics = run.data.metrics
        has_all_metrics = all(
            key in stored_metrics for key in REQUIRED_VALIDATION_METRICS
        )
        try:
            features = json.loads(run.data.params.get("features", "[]"))
        except json.JSONDecodeError:
            features = []

        return {
            "run_id": run.info.run_id,
            "model_type": run.data.params.get("model_type", "NOT_AVAILABLE"),
            "metrics_status": "MEASURED" if has_all_metrics else "NOT_AVAILABLE",
            "metrics_provenance": (
                run.data.params.get("metrics_provenance")
                if has_all_metrics
                else "NOT_AVAILABLE"
            ),
            "rmse": stored_metrics.get("rmse") if has_all_metrics else None,
            "mae": stored_metrics.get("mae") if has_all_metrics else None,
            "r2_score": stored_metrics.get("r2_score") if has_all_metrics else None,
            "features": features if isinstance(features, list) else [],
            "created_at": datetime.fromtimestamp(
                run.info.start_time / 1000, tz=timezone.utc
            ).isoformat(),
        }
    async def predict(self, features: TripFeatures) -> Optional[Prediction]:
        """Predict without inventing confidence evidence."""
        try:
            model = await self.load_best_model()
            if model is None:
                return None
            feature_frame = pd.DataFrame(
                [
                    {
                        "distance_km": features.distance_km,
                        "passenger_count": features.passenger_count,
                        "vendor_id": features.vendor_id,
                        "hour_of_day": features.hour_of_day,
                        "day_of_week": features.day_of_week,
                        "month": features.month,
                        "is_weekend": features.is_weekend,
                        "is_rush_hour": features.is_rush_hour,
                    }
                ]
            )
            duration_minutes = float(model.predict(feature_frame)[0])
            return Prediction(
                predicted_duration_minutes=duration_minutes,
                confidence_score=None,
                confidence_status="NOT_AVAILABLE",
                model_version="latest",
                features_used=features,
                created_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            logger.error("Error en predicción: %s", exc)
            return None
    async def log_experiment(
        self,
        experiment_name: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        artifacts: Dict[str, str] = None,
    ) -> str:
        """Log de experimento completo"""

        with mlflow.start_run(run_name=experiment_name) as run:
            mlflow.log_params(parameters)
            mlflow.log_metrics(metrics)

            if artifacts:
                for artifact_name, artifact_path in artifacts.items():
                    mlflow.log_artifact(artifact_path, artifact_name)

            return run.info.run_id

    async def compare_models(self, limit: int = 10) -> pd.DataFrame:
        """Compara modelos en el experimento"""
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if not experiment:
                return pd.DataFrame()

            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["metrics.rmse ASC"],
                max_results=limit,
            )

            if runs.empty:
                return pd.DataFrame()

            # Seleccionar columnas relevantes
            comparison_columns = [
                "run_id",
                "params.model_type",
                "metrics.rmse",
                "metrics.mae",
                "metrics.r2_score",
                "start_time",
            ]

            available_columns = [
                col for col in comparison_columns if col in runs.columns
            ]
            result = runs[available_columns].copy()

            # Renombrar columnas para mejor legibilidad
            column_mapping = {
                "params.model_type": "model_type",
                "metrics.rmse": "rmse",
                "metrics.mae": "mae",
                "metrics.r2_score": "r2_score",
            }

            result = result.rename(columns=column_mapping)

            return result

        except Exception as e:
            logger.error(f"Error comparando modelos: {e}")
            return pd.DataFrame()
