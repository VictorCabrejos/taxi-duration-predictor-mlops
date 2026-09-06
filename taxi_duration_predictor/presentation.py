"""Pure dashboard boundary: display evidence from one prediction response only."""

from copy import deepcopy
import math


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def prediction_view(payload):
    """Reject inconsistent attribution instead of inventing labels or metrics.

    The dashboard does not select models, read MLflow or estimate durations.
    This is contract validation, not independent verification of a trusted API.
    """
    if not isinstance(payload, dict):
        raise ValueError("Prediction response must be an object")
    model = payload.get("model")
    run_id = payload.get("run_id")
    if (
        not isinstance(model, dict)
        or not isinstance(run_id, str)
        or not run_id
        or model.get("run_id") != run_id
        or payload.get("model_version") != run_id
    ):
        raise ValueError("Prediction and model attribution do not match")
    duration, distance = payload.get("predicted_duration_minutes"), payload.get("distance_km")
    if not _finite(duration) or duration <= 0 or not _finite(distance) or distance < 0:
        raise ValueError("Prediction contains an invalid duration or distance")
    if (
        payload.get("confidence_score") is not None
        or payload.get("confidence_status") != "NOT_AVAILABLE"
    ):
        raise ValueError("This reference does not establish calibrated confidence")
    if (
        model.get("metrics_status") != "MEASURED"
        or model.get("selection_status") != "ELIGIBLE"
        or not isinstance(model.get("provenance"), dict)
        or not isinstance(model.get("artifact_uri"), str)
        or not model["artifact_uri"]
        or any(not _finite(model.get(key)) for key in ("rmse", "mae", "r2_score"))
        or model["rmse"] < 0
        or model["mae"] < 0
    ):
        raise ValueError("Prediction lacks eligible measured model evidence")
    return {
        "duration": f"{duration:.1f} min",
        "distance": f"{distance:.2f} km",
        "confidence": "NOT_AVAILABLE (not calibrated)",
        "run_id": run_id,
        "model": deepcopy(model),
        "features": deepcopy(payload.get("features_used", {})),
        "response": deepcopy(payload),
    }


def request_prediction(post, base_url, payload):
    """One bounded HTTP call; failure is propagated, never replaced by a guess."""
    response = post(base_url.rstrip("/") + "/api/v1/predict/", json=payload, timeout=15)
    response.raise_for_status()
    return prediction_view(response.json())
