"""Reproducible raw-trip training; no dataset or deployment authority is inferred."""

import argparse
import asyncio
import json
import os

import numpy as np
import pandas as pd

from ..adapters.database.data_adapter import PostgreSQLAdapter
from ..adapters.ml.features import TripFeatureTransformer
from ..adapters.ml.mlflow_adapter import MLflowAdapter
from ..adapters.ml.provenance import DatasetDeclaration
from ..adapters.ml.sklearn_adapter import SklearnModelsAdapter
from ..config import Config


class TrainingPipeline:
    def __init__(self, connection_string, mlflow_config=None, sample_size=10000, *, declaration):
        self.data_adapter = PostgreSQLAdapter(connection_string)
        self.ml_adapter = SklearnModelsAdapter()
        self.mlflow_adapter = MLflowAdapter(
            **{"run_id": "", "cohort_id": "", **(mlflow_config or {})}
        )
        self.sample_size = sample_size
        self.declaration = declaration

    async def extract_training_data(self):
        trips = await self.data_adapter.get_trips_for_training(limit=self.sample_size)
        if not trips:
            raise ValueError("No training trips found")
        raw = pd.DataFrame(
            [
                {
                    "pickup_longitude": trip.pickup_location.longitude,
                    "pickup_latitude": trip.pickup_location.latitude,
                    "dropoff_longitude": trip.dropoff_location.longitude,
                    "dropoff_latitude": trip.dropoff_location.latitude,
                    "passenger_count": trip.passenger_count,
                    "vendor_id": trip.vendor_id,
                    "pickup_datetime": trip.pickup_datetime,
                    "trip_duration_seconds": trip.trip_duration.seconds,
                }
                for trip in trips
            ]
        )
        return await self.ml_adapter.prepare_features(raw)

    async def train_all_models(self, X, y):
        results = await self.ml_adapter.train_all_models(X, y, declaration=self.declaration)
        for result in results:
            result["run_id"] = await self.mlflow_adapter.save_model(
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
        return results

    async def run_complete_pipeline(self):
        raw, target = await self.extract_training_data()
        results = await self.train_all_models(raw, target)
        winner = min(results, key=lambda item: (item["metrics"]["rmse"], item["model_name"]))
        loaded = await self.mlflow_adapter.load_selected_model(winner["run_id"])
        np.testing.assert_allclose(
            loaded.model.predict(raw.iloc[:3]), winner["model"].predict(raw.iloc[:3])
        )
        return {
            "models_trained": len(results),
            "best_model": winner["model_name"],
            "best_run_id": loaded.info["run_id"],
            "best_rmse": loaded.info["rmse"],
            "cohort_id": loaded.info["provenance"]["cohort_id"],
            "provenance": loaded.info["provenance"],
        }


def synthetic_raw_trips(rows=300, seed=42):
    """Owned fixture generator; generated labels do not measure NYC accuracy."""
    rng = np.random.default_rng(seed)
    raw = pd.DataFrame(
        {
            "pickup_latitude": rng.uniform(40.65, 40.75, rows),
            "pickup_longitude": rng.uniform(-74.05, -73.98, rows),
            "dropoff_latitude": rng.uniform(40.78, 40.85, rows),
            "dropoff_longitude": rng.uniform(-73.95, -73.8, rows),
            "passenger_count": rng.integers(1, 7, rows),
            "vendor_id": rng.integers(1, 3, rows),
            "pickup_datetime": pd.date_range(
                "2026-01-01T00:00:00", periods=rows, freq="h", tz="America/New_York"
            ),
        }
    )
    features = TripFeatureTransformer().transform(raw)
    minutes = (
        4
        + features["distance_km"] * 2.2
        + features["passenger_count"] * 0.4
        + features["is_rush_hour"] * 3
        + rng.normal(0, 0.3, rows)
    )
    raw["trip_duration_seconds"] = minutes * 60
    return raw


async def bootstrap_training():
    trainer, tracker = SklearnModelsAdapter(), MLflowAdapter(run_id="", cohort_id="")
    declaration = DatasetDeclaration(
        "owned-taxi-fixture-v1", "synthetic", "synthetic_raw_trips(seed=42)", "MIT"
    )
    raw, target = await trainer.prepare_features(synthetic_raw_trips())
    results = await trainer.train_all_models(raw, target, declaration=declaration)
    for result in results:
        result["run_id"] = await tracker.save_model(
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
    winner = min(results, key=lambda item: (item["metrics"]["rmse"], item["model_name"]))
    loaded = await tracker.load_selected_model(winner["run_id"])
    np.testing.assert_allclose(
        loaded.model.predict(raw.iloc[:3]), winner["model"].predict(raw.iloc[:3])
    )
    return {
        "status": "success",
        "models_trained": len(results),
        "synthetic_data": True,
        "best_run_id": winner["run_id"],
        "cohort_id": winner["provenance"]["cohort_id"],
        "model": loaded.info,
    }


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bootstrap", action="store_true", help="Train on owned synthetic raw trips"
    )
    parser.add_argument("--dataset-id")
    parser.add_argument("--source", help="Operator-declared dataset source; never inferred")
    parser.add_argument("--license", help="Operator-declared permission/license reference")
    args = parser.parse_args()
    if args.bootstrap:
        return await bootstrap_training()
    declaration = DatasetDeclaration(args.dataset_id, "operator", args.source, args.license)
    pipeline = TrainingPipeline(Config().require_database_url(), declaration=declaration)
    return await pipeline.run_complete_pipeline()


if __name__ == "__main__":
    # stdout is a machine-readable JSON result, including on Windows terminals.
    os.environ["MLFLOW_SUPPRESS_PRINTING_URL_TO_STDOUT"] = "true"
    print(json.dumps(asyncio.run(main()), indent=2))
