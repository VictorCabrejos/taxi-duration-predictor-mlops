"""
Taxi Duration Predictor - MLOps Pipeline
Arquitectura Hexagonal + DDD + MLflow + AWS PostgreSQL

🎯 Objetivo: Predecir duración de viajes de taxi NYC
🏗️ Arquitectura: Hexagonal simple sin over-engineering
🚀 Stack: FastAPI + MLflow + PostgreSQL + Docker + Streamlit
"""

# Configuración del proyecto
PROJECT_NAME = "taxi_duration_predictor"
VERSION = "1.0.0"
DESCRIPTION = "MLOps Pipeline para predicción de duración de viajes de taxi NYC"

# Configuración de entorno
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuración principal del proyecto"""

    # Base de datos
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/taxi_db"
    )

    # MLflow
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
    mlflow_experiment_name: str = "taxi_duration_prediction"

    # API
    api_host: str = os.getenv("API_HOST", "localhost")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # Modelo
    model_name: str = "taxi_duration_model"
    model_stage: str = "Production"

    # Features
    max_trip_duration_hours: float = 6.0  # Filtrar outliers
    min_trip_duration_seconds: float = 30.0  # Viajes muy cortos

    # NYC boundaries
    nyc_bounds: dict = None

    def __post_init__(self):
        if self.nyc_bounds is None:
            self.nyc_bounds = {
                "lng_min": -74.3,
                "lng_max": -73.7,
                "lat_min": 40.5,
                "lat_max": 40.9,
            }


# Instancia global de configuración
config = Config()
