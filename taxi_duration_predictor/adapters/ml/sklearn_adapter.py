"""Train complete raw-input inference artifacts with attributable holdout evidence."""

from datetime import datetime
from copy import deepcopy

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ...domain.ports import ModelTrainer
from .features import FEATURE_COLUMNS, RAW_COLUMNS, TripFeatureTransformer, canonical_raw
from .provenance import DatasetDeclaration, evaluation_manifest, valid_metrics


class SklearnModelsAdapter(ModelTrainer):
    def get_available_models(self):
        # XGBoost is optional until explicitly selected; the offline reference uses sklearn.
        return {
            "LinearRegression": {
                "model": LinearRegression(),
                "params": {},
                "requires_scaling": True,
            },
            "RandomForest": {
                "model": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=1),
                "params": {"n_estimators": 100, "random_state": 42, "n_jobs": 1},
                "requires_scaling": False,
            },
        }

    async def prepare_features(self, df):
        """Validate raw input and target; the fitted Pipeline owns feature engineering."""
        raw = canonical_raw(df)
        TripFeatureTransformer().transform(raw)
        target = (
            pd.to_numeric(df["trip_duration_seconds"], errors="raise").reset_index(drop=True) / 60
        )
        if not np.isfinite(target).all() or not target.between(0.5, 360).all():
            raise ValueError("Training durations must be finite and between 30 seconds and 6 hours")
        return raw, target

    async def train_model(
        self, model_name, X, y, test_size=0.2, *, declaration: DatasetDeclaration
    ):
        raw = canonical_raw(X)
        target = pd.Series(np.asarray(y, dtype=float)).reset_index(drop=True)
        if len(raw) != len(target) or len(raw) < 10:
            raise ValueError("At least 10 aligned raw trips and targets are required")
        if not np.isfinite(target).all() or not target.between(0.5, 360).all():
            raise ValueError("Training targets must be finite supported durations in minutes")
        config = self.get_available_models().get(model_name)
        if config is None:
            raise ValueError(f"Unsupported model: {model_name}")
        train_indices, validation_indices = train_test_split(
            np.arange(len(raw)), test_size=test_size, random_state=42
        )
        if len(validation_indices) < 2:
            raise ValueError("At least two holdout rows are required for R-squared")
        provenance = evaluation_manifest(raw, target, validation_indices, declaration, test_size)
        model = Pipeline(
            [
                ("features", TripFeatureTransformer()),
                ("preprocessor", StandardScaler() if config["requires_scaling"] else "passthrough"),
                ("estimator", config["model"]),
            ]
        )
        start = datetime.now()
        model.fit(raw.iloc[train_indices], target.iloc[train_indices])
        prediction = model.predict(raw.iloc[validation_indices])
        metrics = {
            "rmse": float(np.sqrt(mean_squared_error(target.iloc[validation_indices], prediction))),
            "mae": float(mean_absolute_error(target.iloc[validation_indices], prediction)),
            "r2_score": float(r2_score(target.iloc[validation_indices], prediction)),
            "training_time_seconds": (datetime.now() - start).total_seconds(),
            "train_size": len(train_indices),
            "test_size": len(validation_indices),
        }
        if not valid_metrics(metrics):
            raise ValueError("Training did not produce finite validation evidence")
        # Persist the evidence *inside* the object as well as in the tracker. Loading
        # verifies both copies so the served object cannot silently borrow another run's metadata.
        model.lifecycle_metadata_ = deepcopy(
            {
                "provenance": provenance,
                "metrics": metrics,
                "model_type": model_name,
                "features": FEATURE_COLUMNS,
                "raw_columns": RAW_COLUMNS,
            }
        )
        return {
            "model": model,
            "model_name": model_name,
            "metrics": metrics,
            "hyperparams": config["params"],
            "features": FEATURE_COLUMNS,
            "provenance": provenance,
        }

    async def train_all_models(self, X, y, *, declaration):
        results = [
            await self.train_model(name, X, y, declaration=declaration)
            for name in self.get_available_models()
        ]
        return sorted(results, key=lambda result: (result["metrics"]["rmse"], result["model_name"]))

    def get_feature_importance(self, model, feature_names):
        estimator = model.named_steps["estimator"]
        values = getattr(estimator, "feature_importances_", None)
        if values is None:
            values = np.abs(getattr(estimator, "coef_", []))
        return dict(zip(feature_names, map(float, values)))
