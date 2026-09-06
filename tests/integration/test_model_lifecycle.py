"""Owned raw trips exercise the actual persistence, selection and HTTP boundary."""

import asyncio
import copy
import json
from types import SimpleNamespace

import numpy as np
import mlflow
import pytest
from fastapi.testclient import TestClient
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from taxi_duration_predictor.adapters.ml.features import TripFeatureTransformer, canonical_raw
from taxi_duration_predictor.adapters.ml.mlflow_adapter import MLflowAdapter, ModelUnavailable
from taxi_duration_predictor.adapters.ml.provenance import DatasetDeclaration, digest
from taxi_duration_predictor.adapters.ml.sklearn_adapter import SklearnModelsAdapter
from taxi_duration_predictor.api import controller
from taxi_duration_predictor.api.main import app
from taxi_duration_predictor.pipeline.train import synthetic_raw_trips


@pytest.fixture(scope="module")
def lifecycle(tmp_path_factory):
    directory = tmp_path_factory.mktemp("lifecycle")
    tracker = MLflowAdapter(
        tracking_uri=f"sqlite:///{(directory / 'tracking.db').as_posix()}",
        experiment_name="owned-raw-trip-lifecycle",
    )
    tracker.client.create_experiment(
        tracker.experiment_name, artifact_location=(directory / "artifacts").as_uri()
    )
    trainer = SklearnModelsAdapter()
    raw, target = asyncio.run(trainer.prepare_features(synthetic_raw_trips(rows=80)))
    declaration = DatasetDeclaration(
        "test-owned-v1", "synthetic", "synthetic_raw_trips(rows=80,seed=42)", "MIT"
    )
    result = asyncio.run(
        trainer.train_model("LinearRegression", raw, target, declaration=declaration)
    )
    run_id = asyncio.run(
        tracker.save_model(
            **{
                key: result[key]
                for key in (
                    "model",
                    "model_name",
                    "metrics",
                    "features",
                    "hyperparams",
                    "provenance",
                )
            }
        )
    )
    return tracker, result, run_id, raw, target


def request_row(raw, index=7):
    record = raw.iloc[index].to_dict()
    record["pickup_datetime"] = record["pickup_datetime"].isoformat()
    return record


def configure_api(monkeypatch, tracker, *, run_id=None, cohort_id=None):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tracker.tracking_uri)
    monkeypatch.setenv("MLFLOW_EXPERIMENT_NAME", tracker.experiment_name)
    for name, value in (("TAXI_MODEL_RUN_ID", run_id), ("TAXI_MODEL_COHORT_ID", cohort_id)):
        if value:
            monkeypatch.setenv(name, value)
        else:
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(controller, "_prediction_pipeline", None)


def test_raw_train_persist_reload_http_prediction_keeps_same_lifecycle(lifecycle, monkeypatch):
    tracker, result, run_id, raw, _ = lifecycle
    configure_api(monkeypatch, tracker)
    loaded = asyncio.run(tracker.load_selected_model())
    assert isinstance(loaded.model, Pipeline)
    assert isinstance(loaded.model.named_steps["features"], TripFeatureTransformer)
    assert isinstance(loaded.model.named_steps["preprocessor"], StandardScaler)
    np.testing.assert_allclose(loaded.model.predict(raw), result["model"].predict(raw), rtol=1e-12)
    with TestClient(app) as client:
        response = client.post("/api/v1/predict/", json=request_row(raw))
        assert response.status_code == 200, response.text
        body = response.json()
        info = client.get("/api/v1/health/model").json()
    assert controller._prediction_pipeline.mlflow_adapter.tracking_uri == tracker.tracking_uri
    assert body["run_id"] == body["model_version"] == info["run_id"] == run_id
    assert body["model"] == info
    assert body["model"]["provenance"] == result["provenance"]
    assert body["model"]["provenance"]["data_kind"] == "synthetic"
    assert body["predicted_duration_minutes"] == pytest.approx(
        result["model"].predict(raw.iloc[[7]])[0]
    )
    assert body["model"]["rmse"] == result["metrics"]["rmse"]
    assert body["confidence_score"] is None
    assert body["confidence_status"] == "NOT_AVAILABLE"
    expected_features = (
        loaded.model.named_steps["features"].transform(raw.iloc[[7]]).iloc[0].to_dict()
    )
    assert body["features_used"] == expected_features


def test_equal_instants_generate_equal_features_and_predictions(lifecycle, monkeypatch):
    tracker, _, _, raw, _ = lifecycle
    configure_api(monkeypatch, tracker)
    request = request_row(raw)
    alternate = {
        **request,
        "pickup_datetime": raw.iloc[7]["pickup_datetime"].tz_convert("UTC").isoformat(),
    }
    with TestClient(app) as client:
        first = client.post("/api/v1/predict/", json=request).json()
        second = client.post("/api/v1/predict/", json=alternate).json()
    assert first["features_used"] == second["features_used"]
    assert first["predicted_duration_minutes"] == second["predicted_duration_minutes"]


def fake_run(result, run_id="run-a", rmse=1.0, *, provenance=None, start_time=1000):
    provenance = provenance or result["provenance"]
    return SimpleNamespace(
        info=SimpleNamespace(
            run_id=run_id, start_time=start_time, status="FINISHED", experiment_id="1"
        ),
        data=SimpleNamespace(
            metrics={**result["metrics"], "rmse": rmse},
            params={
                "model_type": result["model_name"],
                "features": json.dumps(result["features"]),
                "provenance": json.dumps(provenance),
                "cohort_id": provenance["cohort_id"],
                "synthetic_data": str(provenance["data_kind"] == "synthetic").lower(),
                "metrics_provenance": "measured_validation_split",
            },
        ),
    )


def isolated_selector(monkeypatch, lifecycle, runs):
    tracker = MLflowAdapter(
        tracking_uri=lifecycle[0].tracking_uri, experiment_name=lifecycle[0].experiment_name
    )
    tracker.run_id = tracker.cohort_id = None
    monkeypatch.setattr(tracker, "_model_runs", lambda: runs)
    return tracker


def test_incomparable_data_cannot_win_by_low_rmse(lifecycle, monkeypatch):
    _, result, _, _, _ = lifecycle
    operator = {
        **result["provenance"],
        "data_kind": "operator",
        "dataset_id": "fictional-operator-context",
    }
    operator["cohort_id"] = digest(
        {key: value for key, value in operator.items() if key != "cohort_id"}
    )
    synthetic_run, operator_run = (
        fake_run(result, rmse=0.01),
        fake_run(result, "operator-run", 5, provenance=operator),
    )
    tracker = isolated_selector(monkeypatch, lifecycle, [synthetic_run, operator_run])
    with pytest.raises(ModelUnavailable, match="Multiple evaluation cohorts"):
        tracker._best_model_run()
    tracker.cohort_id = operator["cohort_id"]
    assert tracker._best_model_run().info.run_id == "operator-run"


def test_dataset_fingerprint_and_split_prevent_accidental_comparison(lifecycle):
    _, result, _, raw, target = lifecycle
    declaration = DatasetDeclaration(
        "test-owned-v1", "synthetic", "synthetic_raw_trips(rows=80,seed=42)", "MIT"
    )
    changed_target = target.copy()
    changed_target.iloc[0] += 1
    changed = asyncio.run(
        SklearnModelsAdapter().train_model(
            "LinearRegression", raw, changed_target, declaration=declaration
        )
    )
    other_split = asyncio.run(
        SklearnModelsAdapter().train_model(
            "LinearRegression", raw, target, 0.3, declaration=declaration
        )
    )
    assert (
        len(
            {
                result["provenance"]["cohort_id"],
                changed["provenance"]["cohort_id"],
                other_split["provenance"]["cohort_id"],
            }
        )
        == 3
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.0])
def test_nonfinite_or_negative_rmse_is_ineligible(lifecycle, monkeypatch, value):
    result = lifecycle[1]
    invalid, valid = fake_run(result, "invalid", value), fake_run(result, "valid", 3)
    tracker = isolated_selector(monkeypatch, lifecycle, [invalid, valid])
    assert tracker._best_model_run().info.run_id == "valid"
    assert tracker._info(invalid)["metrics_status"] == "NOT_AVAILABLE"


def test_selection_ties_are_stable_and_pinned_cohort_checked(lifecycle, monkeypatch):
    result = lifecycle[1]
    first, second = fake_run(result, "a"), fake_run(result, "b")
    tracker = isolated_selector(monkeypatch, lifecycle, [second, first])
    assert tracker._best_model_run().info.run_id == "a"
    tracker.run_id, tracker.cohort_id = "a", "wrong-cohort"
    monkeypatch.setattr(tracker, "_checked_run", lambda value: first)
    with pytest.raises(ModelUnavailable, match="outside"):
        tracker._best_model_run()


def test_search_pages_until_older_best_is_considered(lifecycle, monkeypatch):
    result = lifecycle[1]
    best = fake_run(result, "oldest-best", 0.01)
    recent = [fake_run(result, f"recent-{index}", 10) for index in range(100)]

    class Page(list):
        def __init__(self, items, token):
            super().__init__(items)
            self.token = token

    tracker = MLflowAdapter(
        tracking_uri=lifecycle[0].tracking_uri, experiment_name=lifecycle[0].experiment_name
    )
    pages = []

    def search(*args, page_token=None, **kwargs):
        pages.append(page_token)
        return Page(recent, "next") if page_token is None else Page([best], None)

    monkeypatch.setattr(tracker.client, "search_runs", search)
    monkeypatch.setattr(
        tracker.client,
        "list_artifacts",
        lambda run_id: [SimpleNamespace(path="model", is_dir=True)],
    )
    assert tracker._best_model_run().info.run_id == "oldest-best"
    assert pages == [None, "next"]


def test_complete_legacy_metrics_are_inspectable_but_never_served(lifecycle, monkeypatch):
    legacy = fake_run(lifecycle[1], "legacy")
    legacy.data.params.pop("provenance")
    legacy.data.params.pop("metrics_provenance")
    tracker = isolated_selector(monkeypatch, lifecycle, [legacy])
    tracker.run_id = "legacy"
    monkeypatch.setattr(tracker, "_checked_run", lambda run_id: legacy)
    monkeypatch.setattr(controller, "_prediction_pipeline", SimpleNamespace(mlflow_adapter=tracker))
    with TestClient(app) as client:
        response = client.get("/api/v1/health/model")
    assert response.status_code == 200
    assert response.json()["metrics_provenance"] == "NOT_AVAILABLE"
    assert response.json()["rmse"] is None
    with pytest.raises(ModelUnavailable, match="lacks verified"):
        tracker._best_model_run()


def test_artifact_cannot_borrow_changed_run_metrics(lifecycle, monkeypatch):
    tracker, result, run_id, _, _ = lifecycle
    altered = copy.deepcopy(tracker.client.get_run(run_id))
    altered.data.metrics["rmse"] = result["metrics"]["rmse"] + 1
    monkeypatch.setattr(tracker, "_best_model_run", lambda: altered)
    with pytest.raises(ModelUnavailable, match="metadata do not agree"):
        asyncio.run(tracker.load_selected_model())


def test_prediction_retains_selected_identity_when_new_run_arrives(lifecycle, monkeypatch):
    tracker, _, run_id, raw, _ = lifecycle
    configure_api(monkeypatch, tracker)
    pipeline = asyncio.run(controller.get_prediction_pipeline())
    run = pipeline.mlflow_adapter.client.get_run(run_id)
    calls = []

    def select_once():
        calls.append(1)
        if len(calls) > 1:
            raise AssertionError("Prediction reselected its metadata")
        return run

    monkeypatch.setattr(pipeline.mlflow_adapter, "_best_model_run", select_once)
    with TestClient(app) as client:
        body = client.post("/api/v1/predict/", json=request_row(raw)).json()
    assert body["run_id"] == body["model"]["run_id"] == run_id
    assert len(calls) == 1


def test_missing_model_returns_503_without_heuristic(lifecycle, monkeypatch):
    tracker, _, _, raw, _ = lifecycle
    configure_api(monkeypatch, tracker, run_id="missing-run")
    with TestClient(app) as client:
        response = client.post("/api/v1/predict/", json=request_row(raw))
    assert response.status_code == 503
    assert "predicted_duration_minutes" not in response.json()


def test_invalid_output_is_not_success(lifecycle, monkeypatch):
    tracker, _, _, raw, _ = lifecycle
    configure_api(monkeypatch, tracker)
    pipeline = asyncio.run(controller.get_prediction_pipeline())
    loaded = asyncio.run(pipeline.mlflow_adapter.load_selected_model())
    monkeypatch.setattr(loaded.model, "predict", lambda raw: [float("nan")])

    async def load():
        return loaded

    monkeypatch.setattr(pipeline.mlflow_adapter, "load_selected_model", load)
    with TestClient(app) as client:
        response = client.post("/api/v1/predict/", json=request_row(raw))
    assert response.status_code == 503


@pytest.mark.parametrize("timestamp", ["2026-03-08T02:30:00", "2026-11-01T01:30:00"])
def test_ambiguous_or_nonexistent_naive_nyc_time_rejected(lifecycle, timestamp):
    raw = lifecycle[3].iloc[[0]].copy()
    raw["pickup_datetime"] = timestamp
    with pytest.raises(ValueError, match="pickup timestamp"):
        canonical_raw(raw)


def test_save_rejects_unbound_evidence_before_creating_run(lifecycle):
    tracker, result, _, _, _ = lifecycle
    with pytest.raises(ValueError, match="Artifact metadata differs"):
        asyncio.run(
            tracker.save_model(
                result["model"],
                result["model_name"],
                {**result["metrics"], "rmse": 0.01},
                result["features"],
                provenance=result["provenance"],
            )
        )


def test_artifact_download_uses_own_store_and_restores_global_state(lifecycle, tmp_path):
    tracker, _, run_id, _, _ = lifecycle
    previous = mlflow.get_tracking_uri()
    other_store = f"sqlite:///{(tmp_path / 'unrelated.db').as_posix()}"
    try:
        mlflow.set_tracking_uri(other_store)
        assert asyncio.run(tracker.load_selected_model()).info["run_id"] == run_id
        assert mlflow.get_tracking_uri() == other_store
    finally:
        mlflow.set_tracking_uri(previous)


def test_training_result_mutation_does_not_relabel_artifact(lifecycle):
    tracker, result, _, _, _ = lifecycle
    changed = copy.deepcopy(result)
    changed["metrics"]["rmse"] = 0.001
    with pytest.raises(ValueError, match="Artifact metadata differs"):
        asyncio.run(
            tracker.save_model(
                **{
                    key: changed[key]
                    for key in (
                        "model",
                        "model_name",
                        "metrics",
                        "features",
                        "hyperparams",
                        "provenance",
                    )
                }
            )
        )


def test_explicit_artifact_load_cannot_override_serving_policy(lifecycle, monkeypatch):
    tracker, _, run_id, _, _ = lifecycle
    monkeypatch.setattr(tracker, "cohort_id", "different-cohort")
    with pytest.raises(ModelUnavailable, match="outside"):
        asyncio.run(tracker.load_selected_model(run_id))


def test_model_valueerror_is_service_failure_not_invalid_request(lifecycle, monkeypatch):
    tracker, _, _, raw, _ = lifecycle
    configure_api(monkeypatch, tracker)
    pipeline = asyncio.run(controller.get_prediction_pipeline())
    loaded = asyncio.run(pipeline.mlflow_adapter.load_selected_model())

    def broken_model(raw):
        raise ValueError("Internal model feature mismatch")

    monkeypatch.setattr(loaded.model, "predict", broken_model)

    async def load():
        return loaded

    monkeypatch.setattr(pipeline.mlflow_adapter, "load_selected_model", load)
    with TestClient(app) as client:
        response = client.post("/api/v1/predict/", json=request_row(raw))
    assert response.status_code == 503
