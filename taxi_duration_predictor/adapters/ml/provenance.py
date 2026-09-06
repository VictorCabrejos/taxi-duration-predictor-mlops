"""Content-addressed evaluation cohorts; declarations never certify data ownership."""

import hashlib
import json
import math
from dataclasses import asdict, dataclass

import pandas as pd

from .features import FEATURE_IMPLEMENTATION_SHA256, FEATURE_VERSION, canonical_raw

VALIDATION_METRICS = ("rmse", "mae", "r2_score")


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def data_digest(raw, target) -> str:
    frame = canonical_raw(raw)
    frame["pickup_datetime"] = frame["pickup_datetime"].map(lambda value: value.isoformat())
    frame["duration_minutes"] = list(map(float, target))
    return digest(frame.to_dict(orient="records"))


@dataclass(frozen=True)
class DatasetDeclaration:
    dataset_id: str
    data_kind: str
    source: str
    license: str

    def __post_init__(self):
        if self.data_kind not in {"synthetic", "operator"}:
            raise ValueError("data_kind must be synthetic or operator")
        if any(not isinstance(value, str) or not value.strip() for value in asdict(self).values()):
            raise ValueError("Dataset identity, source and license declarations are required")


def evaluation_manifest(raw, target, validation_indices, declaration, test_size):
    raw = canonical_raw(raw)
    target = pd.Series(target).reset_index(drop=True)
    evidence = {
        **asdict(declaration),
        "dataset_sha256": data_digest(raw, target),
        "evaluation_sha256": data_digest(
            raw.iloc[validation_indices], target.iloc[validation_indices]
        ),
        "feature_version": FEATURE_VERSION,
        "feature_implementation_sha256": FEATURE_IMPLEMENTATION_SHA256,
        "target_unit": "minutes",
        "split_method": "seeded_random_holdout",
        "split_seed": 42,
        "test_fraction": float(test_size),
        "row_count": len(raw),
        "validation_rows": len(validation_indices),
    }
    return {**evidence, "cohort_id": digest(evidence)}


def valid_metrics(metrics):
    try:
        return (
            all(math.isfinite(float(metrics[key])) for key in VALIDATION_METRICS)
            and float(metrics["rmse"]) >= 0
            and float(metrics["mae"]) >= 0
            and float(metrics["r2_score"]) <= 1
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def valid_manifest(value):
    try:
        DatasetDeclaration(
            **{key: value[key] for key in ("dataset_id", "data_kind", "source", "license")}
        )
        evidence = {key: item for key, item in value.items() if key != "cohort_id"}
        return (
            value["cohort_id"] == digest(evidence)
            and value["feature_version"] == FEATURE_VERSION
            and value["feature_implementation_sha256"] == FEATURE_IMPLEMENTATION_SHA256
            and value["target_unit"] == "minutes"
            and value["split_method"] == "seeded_random_holdout"
            and value["split_seed"] == 42
            and 0 < value["test_fraction"] < 1
            and 2 <= value["validation_rows"] < value["row_count"]
            and all(
                len(value[key]) == 64 and all(c in "0123456789abcdef" for c in value[key])
                for key in ("dataset_sha256", "evaluation_sha256")
            )
        )
    except (KeyError, TypeError, ValueError):
        return False
