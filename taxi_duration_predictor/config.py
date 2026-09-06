"""Environment-backed configuration for the Taxi MLOps reference system."""

import os
from dataclasses import dataclass, field

PROJECT_NAME = "taxi_duration_predictor"
VERSION = "1.0.0"
DESCRIPTION = "MLOps reference pipeline for NYC taxi-trip duration prediction"


@dataclass
class Config:
    """Runtime configuration with no functional credential defaults."""

    database_url: str | None = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    mlflow_tracking_uri: str = field(
        default_factory=lambda: os.getenv("MLFLOW_TRACKING_URI", "sqlite:///data/mlflow.db")
    )
    mlflow_experiment_name: str = field(
        default_factory=lambda: os.getenv("MLFLOW_EXPERIMENT_NAME", "taxi_duration_prediction")
    )
    model_cohort_id: str | None = field(default_factory=lambda: os.getenv("TAXI_MODEL_COHORT_ID"))
    model_run_id: str | None = field(default_factory=lambda: os.getenv("TAXI_MODEL_RUN_ID"))
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "localhost"))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    model_name: str = "taxi_duration_model"
    model_stage: str = "Production"
    max_trip_duration_hours: float = 6.0
    min_trip_duration_seconds: float = 30.0
    nyc_bounds: dict[str, float] = field(
        default_factory=lambda: {
            "lng_min": -74.3,
            "lng_max": -73.7,
            "lat_min": 40.5,
            "lat_max": 40.9,
        }
    )

    def require_database_url(self) -> str:
        """Return the database URL or fail before an adapter attempts to connect."""
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is required for PostgreSQL operations")
        return self.database_url


config = Config()
