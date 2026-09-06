"""One versioned raw-trip transformation, serialized inside every inference artifact."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

FEATURE_VERSION = "nyc-haversine-local-time-v1"
# Pickled transformers reference installed Python code. Reject artifacts when that
# implementation changes, including an accidental change without a version bump.
FEATURE_IMPLEMENTATION_SHA256 = hashlib.sha256(
    Path(__file__).read_text(encoding="utf-8").encode()
).hexdigest()
RAW_COLUMNS = [
    "pickup_latitude",
    "pickup_longitude",
    "dropoff_latitude",
    "dropoff_longitude",
    "passenger_count",
    "vendor_id",
    "pickup_datetime",
]
FEATURE_COLUMNS = [
    "distance_km",
    "passenger_count",
    "vendor_id",
    "hour_of_day",
    "day_of_week",
    "month",
    "is_weekend",
    "is_rush_hour",
]


def local_timestamp(value):
    """Naive inputs mean NYC wall time; offset-aware inputs describe an instant."""
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        raise ValueError("pickup_datetime must be a valid timestamp")
    if timestamp.tzinfo is None:
        # Reject ambiguous/nonexistent wall times instead of guessing a DST offset.
        return timestamp.tz_localize("America/New_York")
    return timestamp.tz_convert("America/New_York")


def canonical_raw(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(RAW_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing raw trip columns: {sorted(missing)}")
    result = frame[RAW_COLUMNS].copy().reset_index(drop=True)
    if result.empty:
        raise ValueError("At least one raw trip is required")
    numeric = RAW_COLUMNS[:-1]
    try:
        result[numeric] = result[numeric].astype(float)
        timestamps = [local_timestamp(value) for value in result["pickup_datetime"]]
    except Exception as exc:
        raise ValueError("Invalid numeric trip field or NYC pickup timestamp") from exc
    if not np.isfinite(result[numeric].to_numpy()).all():
        raise ValueError("Raw trip values must be finite")
    for name in ("pickup_latitude", "dropoff_latitude"):
        if not result[name].between(40.5, 40.9).all():
            raise ValueError(f"{name} is outside supported NYC bounds")
    for name in ("pickup_longitude", "dropoff_longitude"):
        if not result[name].between(-74.3, -73.7).all():
            raise ValueError(f"{name} is outside supported NYC bounds")
    if not result["passenger_count"].isin(range(1, 7)).all():
        raise ValueError("passenger_count must be an integer from 1 to 6")
    if not result["vendor_id"].isin([1, 2]).all():
        raise ValueError("vendor_id must be 1 or 2")
    result["pickup_datetime"] = pd.DatetimeIndex(timestamps)
    return result


class TripFeatureTransformer(TransformerMixin, BaseEstimator):
    """Deterministic feature definition shared by fitting and HTTP inference."""

    def fit(self, X, y=None):
        canonical_raw(X)
        self.feature_names_in_ = np.asarray(RAW_COLUMNS, dtype=object)
        self.n_features_in_ = len(RAW_COLUMNS)
        return self

    def transform(self, X):
        raw = canonical_raw(X)
        lat1, lon1, lat2, lon2 = (np.radians(raw[name]) for name in RAW_COLUMNS[:4])
        a = (
            np.sin((lat2 - lat1) / 2) ** 2
            + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
        )
        distance = 6371 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
        if (distance < 0.1).any():
            raise ValueError("Supported trips must span at least 100 metres")
        hour = raw["pickup_datetime"].dt.hour
        day = raw["pickup_datetime"].dt.dayofweek
        return pd.DataFrame(
            {
                "distance_km": distance,
                "passenger_count": raw["passenger_count"],
                "vendor_id": raw["vendor_id"],
                "hour_of_day": hour,
                "day_of_week": day,
                "month": raw["pickup_datetime"].dt.month,
                "is_weekend": day.isin([5, 6]).astype(int),
                "is_rush_hour": hour.isin([7, 8, 9, 17, 18, 19]).astype(int),
            }
        )[FEATURE_COLUMNS]

    def get_feature_names_out(self, input_features=None):
        return np.asarray(FEATURE_COLUMNS, dtype=object)
