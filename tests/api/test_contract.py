import asyncio

from taxi_duration_predictor.api.main import app, simple_health


def test_service_local_health_contract() -> None:
    response = asyncio.run(simple_health())
    schema = app.openapi()

    assert response["status"] == "ok"
    assert "/health" in schema["paths"]


def test_openapi_describes_reference_boundaries() -> None:
    schema = app.openapi()
    description = schema["info"]["description"]

    assert schema["info"]["title"] == "Taxi Duration Predictor API"
    assert "No incluye un dataset de NYC" in description
    assert "49,000+" not in description
    assert "listo para producción" in description
