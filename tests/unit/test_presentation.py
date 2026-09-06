"""Consumer truthfulness under absent, inconsistent and failed API evidence."""

import pytest

from taxi_duration_predictor.presentation import prediction_view, request_prediction


@pytest.fixture
def response():
    return {
        "predicted_duration_minutes": 12.5,
        "distance_km": 3.2,
        "confidence_score": None,
        "confidence_status": "NOT_AVAILABLE",
        "run_id": "run-A",
        "model_version": "run-A",
        "features_used": {"hour": 8},
        "model": {
            "run_id": "run-A",
            "artifact_uri": "runs:/run-A/model",
            "metrics_status": "MEASURED",
            "selection_status": "ELIGIBLE",
            "rmse": 2.4,
            "mae": 1.2,
            "r2_score": -0.2,
            "provenance": {"data_kind": "synthetic", "cohort_id": "cohort-A"},
        },
    }


def test_null_confidence_and_negative_measured_r2_are_displayable(response):
    view = prediction_view(response)
    assert view["confidence"] == "NOT_AVAILABLE (not calibrated)"
    assert view["duration"] == "12.5 min"
    assert view["model"]["r2_score"] == -0.2


def test_model_snapshot_is_bound_to_response_not_later_selection(response):
    view = prediction_view(response)
    response["model"]["run_id"] = "run-B"
    response["model"]["provenance"]["cohort_id"] = "cohort-B"
    assert view["model"]["run_id"] == view["run_id"] == "run-A"
    assert view["model"]["provenance"]["cohort_id"] == "cohort-A"


@pytest.mark.parametrize(
    "key,value",
    [
        ("run_id", "other"),
        ("metrics_status", "NOT_AVAILABLE"),
        ("selection_status", "LEGACY_OR_INVALID"),
        ("rmse", None),
        ("mae", float("nan")),
        ("r2_score", float("inf")),
        ("provenance", None),
    ],
)
def test_inconsistent_or_missing_evidence_is_not_displayed(response, key, value):
    response["model"][key] = value
    with pytest.raises(ValueError):
        prediction_view(response)


@pytest.mark.parametrize(
    "key,value",
    [
        ("model_version", "other"),
        ("confidence_score", 0.85),
        ("confidence_status", "MEASURED"),
        ("predicted_duration_minutes", 0),
        ("distance_km", float("nan")),
    ],
)
def test_no_fabricated_prediction_or_confidence(response, key, value):
    response[key] = value
    with pytest.raises(ValueError):
        prediction_view(response)


def test_http_error_does_not_parse_body_or_fallback():
    class FailedResponse:
        def raise_for_status(self):
            raise RuntimeError("503 unavailable")

        def json(self):
            pytest.fail("Do not render an unsuccessful response")

    with pytest.raises(RuntimeError, match="503"):
        request_prediction(lambda *args, **kwargs: FailedResponse(), "http://api", {})


def test_exactly_one_bounded_request_no_second_model_query(response):
    calls = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return response

    def post(*args, **kwargs):
        calls.append((args, kwargs))
        return Response()

    assert request_prediction(post, "http://api/", {"vendor_id": 1})["run_id"] == "run-A"
    assert calls == [(("http://api/api/v1/predict/",), {"json": {"vendor_id": 1}, "timeout": 15})]
