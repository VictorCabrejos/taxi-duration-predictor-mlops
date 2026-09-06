"""Render the actual Streamlit consumer against deterministic HTTP responses."""

from pathlib import Path

import requests
from streamlit.testing.v1 import AppTest


DASHBOARD = Path(__file__).parents[2] / "observability/dashboards/enhanced_dashboard.py"


def payload():
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


def response(body, status=200):
    class Response:
        status_code = status

        def raise_for_status(self):
            if status != 200:
                raise requests.HTTPError(response=self)

        def json(self):
            return body

    return Response()


def test_actual_dashboard_renders_null_confidence_and_response_attribution(monkeypatch):
    calls = []

    def post(*args, **kwargs):
        calls.append((args, kwargs))
        return response(payload())

    monkeypatch.setattr(requests, "post", post)
    app = AppTest.from_file(str(DASHBOARD)).run()
    assert not calls  # startup does not probe a database/tracker or make up readiness
    app.button[0].click().run()
    assert not app.exception
    assert [metric.value for metric in app.metric] == [
        "12.5 min",
        "3.20 km",
        "NOT_AVAILABLE (not calibrated)",
    ]
    assert app.text[0].value == "Exact run: run-A"
    assert len(calls) == 1


def test_failed_second_request_clears_previous_success_without_heuristic(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: response(payload()))
    app = AppTest.from_file(str(DASHBOARD)).run()
    app.button[0].click().run()
    assert len(app.metric) == 3
    monkeypatch.setattr(requests, "post", lambda *a, **kw: response({}, 503))
    app.button[0].click().run()
    assert not app.exception
    assert not app.metric
    assert len(app.error) == 1 and "503" in app.error[0].value
    assert "No estimate was substituted" in app.error[0].value


def test_inconsistent_response_is_not_rendered_as_a_prediction(monkeypatch):
    body = payload()
    body["model"]["run_id"] = "another-run"
    monkeypatch.setattr(requests, "post", lambda *a, **kw: response(body))
    app = AppTest.from_file(str(DASHBOARD)).run()
    app.button[0].click().run()
    assert not app.exception
    assert not app.metric
    assert len(app.error) == 1
