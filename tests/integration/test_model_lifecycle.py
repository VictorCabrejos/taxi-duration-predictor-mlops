import asyncio
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from taxi_duration_predictor.adapters.ml.mlflow_adapter import MLflowAdapter
from taxi_duration_predictor.adapters.ml.sklearn_adapter import SklearnModelsAdapter
from taxi_duration_predictor.api.controller import model_info


def _synthetic_training_data() -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(20260905)
    rows = 80
    features = pd.DataFrame(
        {
            "distance_km": rng.uniform(0.5, 30.0, rows),
            "passenger_count": rng.integers(1, 7, rows),
            "vendor_id": rng.integers(1, 3, rows),
            "hour_of_day": rng.integers(0, 24, rows),
            "day_of_week": rng.integers(0, 7, rows),
            "month": rng.integers(1, 13, rows),
            "is_weekend": rng.integers(0, 2, rows),
            "is_rush_hour": rng.integers(0, 2, rows),
        }
    )
    target = (
        4.0
        + 2.2 * features["distance_km"]
        + 0.4 * features["passenger_count"]
        + 3.0 * features["is_rush_hour"]
    )
    return features, target


def test_train_save_reload_predict_and_model_info_are_artifact_linked(tmp_path) -> None:
    tracking_root = tmp_path / "mlruns"
    tracking_root.mkdir()
    tracker = MLflowAdapter(
        tracking_uri=tracking_root.as_uri(),
        experiment_name="lifecycle-regression",
    )
    features, target = _synthetic_training_data()
    trainer = SklearnModelsAdapter()

    result = asyncio.run(trainer.train_model("LinearRegression", features, target))
    probe = features.iloc[[7]].copy()
    in_memory_prediction = result["model"].predict(probe)
    run_id = asyncio.run(
        tracker.save_model(
            model=result["model"],
            model_name=result["model_name"],
            metrics=result["metrics"],
            features=result["features"],
            hyperparams=result["hyperparams"],
        )
    )

    reloaded_model = asyncio.run(tracker.load_best_model())
    assert isinstance(reloaded_model, Pipeline)
    assert isinstance(reloaded_model.named_steps["preprocessor"], StandardScaler)
    np.testing.assert_allclose(
        reloaded_model.predict(probe), in_memory_prediction, rtol=1e-12, atol=1e-12
    )

    stored_info = asyncio.run(tracker.get_model_info())
    assert stored_info is not None
    assert stored_info["run_id"] == run_id
    assert stored_info["metrics_status"] == "MEASURED"
    assert stored_info["metrics_provenance"] == "measured_validation_split"
    assert stored_info["rmse"] == pytest.approx(result["metrics"]["rmse"])
    assert stored_info["mae"] == pytest.approx(result["metrics"]["mae"])
    assert stored_info["r2_score"] == pytest.approx(result["metrics"]["r2_score"])

    response = asyncio.run(
        model_info(pipeline=SimpleNamespace(mlflow_adapter=tracker))
    )
    assert response.run_id == run_id
    assert response.metrics_status == "MEASURED"
    assert response.rmse == pytest.approx(result["metrics"]["rmse"])


def test_incomplete_artifact_metrics_are_explicitly_unavailable(
    tmp_path, monkeypatch
) -> None:
    tracking_root = tmp_path / "empty-mlruns"
    tracking_root.mkdir()
    tracker = MLflowAdapter(
        tracking_uri=tracking_root.as_uri(),
        experiment_name="missing-metrics-regression",
    )
    with pytest.raises(ValueError, match="Missing measured validation metrics"):
        asyncio.run(
            tracker.save_model(
                model=object(),
                model_name="IncompleteModel",
                metrics={"rmse": 1.25},
                features=[],
            )
        )
    incomplete_run = SimpleNamespace(
        info=SimpleNamespace(run_id="incomplete-run", start_time=1_700_000_000_000),
        data=SimpleNamespace(
            metrics={"rmse": 1.25},
            params={"model_type": "LinearRegression", "features": "[]"},
        ),
    )
    monkeypatch.setattr(tracker, "_best_model_run", lambda: incomplete_run)

    stored_info = asyncio.run(tracker.get_model_info())

    assert stored_info["metrics_status"] == "NOT_AVAILABLE"
    assert stored_info["metrics_provenance"] == "NOT_AVAILABLE"
    assert stored_info["rmse"] is None
    assert stored_info["mae"] is None
    assert stored_info["r2_score"] is None
