import pytest

from taxi_duration_predictor.config import Config


def test_database_url_has_no_embedded_fallback(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    config = Config()

    assert config.database_url is None
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        config.require_database_url()


def test_database_url_is_read_from_environment(monkeypatch) -> None:
    value = "postgresql://example.invalid/taxi"
    monkeypatch.setenv("DATABASE_URL", value)

    assert Config().require_database_url() == value
