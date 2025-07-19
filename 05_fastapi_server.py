# 🚀 FastAPI Prediction Server
# FASE 4B: API REST para Predicciones de Duración de Viajes

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import pandas as pd
import numpy as np
import asyncio
import asyncpg
from datetime import datetime
import logging
import uvicorn
from typing import Optional
import warnings

warnings.filterwarnings("ignore")

# 🔧 Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🎯 Inicializar FastAPI
app = FastAPI(
    title="🚕 Taxi Duration Predictor API",
    description="API REST para predicciones de duración de viajes usando MLflow + ML",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 🌐 Configurar CORS para integrarse con Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🗄️ Configuración de base de datos
AWS_ENDPOINT = "taxi-duration-db.ckj7uy651uld.us-east-1.rds.amazonaws.com"
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "taxiuser"
DB_PASSWORD = "TaxiDB2025!"

# 📊 Configuración MLflow
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
EXPERIMENT_NAME = "taxi_duration_prediction"

# 🤖 Variables globales para modelo
loaded_model = None
model_metadata = None
model_features = [
    "distance_km",
    "passenger_count",
    "vendor_id",
    "hour_of_day",
    "day_of_week",
    "month",
    "is_weekend",
    "is_rush_hour",
]


# 📝 Modelos Pydantic para requests
class TripPredictionRequest(BaseModel):
    """Modelo para request de predicción de viaje"""

    pickup_latitude: float = Field(..., ge=-90, le=90, description="Latitud de pickup")
    pickup_longitude: float = Field(
        ..., ge=-180, le=180, description="Longitud de pickup"
    )
    dropoff_latitude: float = Field(
        ..., ge=-90, le=90, description="Latitud de dropoff"
    )
    dropoff_longitude: float = Field(
        ..., ge=-180, le=180, description="Longitud de dropoff"
    )
    passenger_count: int = Field(..., ge=1, le=6, description="Número de pasajeros")
    vendor_id: int = Field(..., ge=1, le=2, description="ID del vendor")
    pickup_hour: int = Field(..., ge=0, le=23, description="Hora de pickup (0-23)")
    day_of_week: int = Field(
        ..., ge=0, le=6, description="Día de la semana (0=Lunes, 6=Domingo)"
    )
    month: int = Field(..., ge=1, le=12, description="Mes del año")

    class Config:
        schema_extra = {
            "example": {
                "pickup_latitude": 40.7589,
                "pickup_longitude": -73.9851,
                "dropoff_latitude": 40.7505,
                "dropoff_longitude": -73.9934,
                "passenger_count": 2,
                "vendor_id": 1,
                "pickup_hour": 14,
                "day_of_week": 2,
                "month": 7,
            }
        }


class TripPredictionResponse(BaseModel):
    """Modelo para response de predicción"""

    predicted_duration_minutes: float = Field(
        ..., description="Duración predicha en minutos"
    )
    distance_km: float = Field(..., description="Distancia calculada en kilómetros")
    model_type: str = Field(..., description="Tipo de modelo usado")
    model_version: str = Field(..., description="Versión del modelo")
    confidence_score: float = Field(..., description="Score de confianza")
    features_used: dict = Field(
        ..., description="Features utilizadas para la predicción"
    )
    prediction_timestamp: datetime = Field(
        ..., description="Timestamp de la predicción"
    )


class HealthResponse(BaseModel):
    """Modelo para health check"""

    status: str = Field(..., description="Estado del servicio")
    timestamp: datetime = Field(..., description="Timestamp del check")
    model_loaded: bool = Field(..., description="Si el modelo está cargado")
    model_info: Optional[dict] = Field(None, description="Información del modelo")
    database_status: str = Field(..., description="Estado de la base de datos")


# 🛠️ Funciones utilitarias
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia haversine entre dos puntos geográficos"""
    R = 6371  # Radio de la Tierra en km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def engineer_features(request: TripPredictionRequest) -> dict:
    """Crea features engineered desde el request"""
    # 1. Calcular distancia
    distance_km = haversine_distance(
        request.pickup_latitude,
        request.pickup_longitude,
        request.dropoff_latitude,
        request.dropoff_longitude,
    )

    # 2. Features categóricas
    is_weekend = 1 if request.day_of_week >= 5 else 0
    is_rush_hour = 1 if request.pickup_hour in [7, 8, 9, 17, 18, 19] else 0

    # 3. Compilar features
    features = {
        "distance_km": distance_km,
        "passenger_count": request.passenger_count,
        "vendor_id": request.vendor_id,
        "hour_of_day": request.pickup_hour,
        "day_of_week": request.day_of_week,
        "month": request.month,
        "is_weekend": is_weekend,
        "is_rush_hour": is_rush_hour,
    }

    return features


async def load_best_model():
    """Carga el mejor modelo desde MLflow"""
    global loaded_model, model_metadata

    try:
        # Configurar MLflow
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        client = MlflowClient()

        # Obtener experimento
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        if not experiment:
            raise Exception(f"Experimento {EXPERIMENT_NAME} no encontrado")

        # Obtener todas las runs y encontrar la mejor
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id], order_by=["metrics.rmse ASC"]
        )

        if not runs:
            raise Exception("No hay runs disponibles en el experimento")

        best_run = runs[0]
        run_id = best_run.info.run_id

        # Cargar modelo
        model_uri = f"runs:/{run_id}/model"
        loaded_model = mlflow.sklearn.load_model(model_uri)

        # Guardar metadata
        model_metadata = {
            "run_id": run_id,
            "model_type": best_run.data.params.get("model_type", "Unknown"),
            "rmse": float(best_run.data.metrics.get("rmse", 0)),
            "mae": float(best_run.data.metrics.get("mae", 0)),
            "r2_score": float(best_run.data.metrics.get("r2_score", 0)),
            "train_size": int(best_run.data.params.get("train_size", 0)),
            "loaded_at": datetime.now().isoformat(),
        }

        logger.info(
            f"✅ Modelo cargado: {model_metadata['model_type']} (RMSE: {model_metadata['rmse']:.2f})"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Error cargando modelo: {e}")
        return False


async def check_database_connection():
    """Verifica conexión a la base de datos"""
    try:
        conn = await asyncpg.connect(
            host=AWS_ENDPOINT,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )

        # Test query
        result = await conn.fetchval("SELECT COUNT(*) FROM taxi_trips")
        await conn.close()

        return {"status": "connected", "total_trips": result}

    except Exception as e:
        logger.error(f"❌ Error de base de datos: {e}")
        return {"status": "error", "error": str(e)}


# 🚀 Eventos de startup
@app.on_event("startup")
async def startup_event():
    """Inicialización del servidor"""
    logger.info("🚀 Iniciando Taxi Duration Predictor API...")

    # Cargar modelo
    model_loaded = await load_best_model()
    if not model_loaded:
        logger.warning("⚠️ Servidor iniciado sin modelo cargado")

    logger.info("✅ API lista para recibir requests")


# 📍 Endpoints
@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz con información del API"""
    return {
        "message": "🚕 Taxi Duration Predictor API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "predict": "/predict",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check completo del sistema"""
    # Verificar base de datos
    db_status = await check_database_connection()

    return HealthResponse(
        status=(
            "healthy"
            if loaded_model and db_status["status"] == "connected"
            else "degraded"
        ),
        timestamp=datetime.now(),
        model_loaded=loaded_model is not None,
        model_info=model_metadata,
        database_status=db_status["status"],
    )


@app.post("/predict", response_model=TripPredictionResponse, tags=["Predictions"])
async def predict_trip_duration(request: TripPredictionRequest):
    """Predice la duración de un viaje de taxi"""

    # Verificar que el modelo esté cargado
    if loaded_model is None:
        raise HTTPException(
            status_code=503, detail="Modelo no disponible. Intentando cargar..."
        )

    try:
        # 1. Engineer features
        features = engineer_features(request)

        # 2. Preparar datos para predicción
        feature_array = np.array([[features[col] for col in model_features]])

        # 3. Hacer predicción
        prediction = loaded_model.predict(feature_array)[0]

        # 4. Calcular confidence score (simplificado)
        confidence = 0.85 if not features["is_rush_hour"] else 0.75
        if features["distance_km"] > 50:  # Viajes muy largos tienen menos confianza
            confidence *= 0.9

        # 5. Log de la predicción (para monitoring futuro)
        logger.info(
            f"Predicción: {prediction:.2f} min, Distancia: {features['distance_km']:.2f} km"
        )

        return TripPredictionResponse(
            predicted_duration_minutes=round(prediction, 2),
            distance_km=round(features["distance_km"], 2),
            model_type=model_metadata["model_type"],
            model_version=model_metadata["run_id"][:8],
            confidence_score=round(confidence, 3),
            features_used=features,
            prediction_timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"❌ Error en predicción: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error procesando predicción: {str(e)}"
        )


@app.get("/model/info", tags=["Model"])
async def get_model_info():
    """Obtiene información detallada del modelo actual"""
    if model_metadata is None:
        raise HTTPException(status_code=404, detail="No hay modelo cargado")

    return {
        "model_metadata": model_metadata,
        "features_required": model_features,
        "model_loaded": loaded_model is not None,
    }


@app.post("/model/reload", tags=["Model"])
async def reload_model():
    """Recarga el mejor modelo desde MLflow"""
    success = await load_best_model()

    if success:
        return {
            "status": "success",
            "message": "Modelo recargado exitosamente",
            "model_info": model_metadata,
        }
    else:
        raise HTTPException(status_code=500, detail="Error recargando modelo")


@app.get("/stats/database", tags=["Statistics"])
async def get_database_stats():
    """Obtiene estadísticas de la base de datos"""
    db_status = await check_database_connection()

    if db_status["status"] != "connected":
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        conn = await asyncpg.connect(
            host=AWS_ENDPOINT,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )

        stats = await conn.fetchrow(
            """
            SELECT
                COUNT(*) as total_trips,
                AVG(trip_duration_seconds) as avg_duration_seconds,
                MIN(pickup_datetime) as earliest_trip,
                MAX(pickup_datetime) as latest_trip
            FROM taxi_trips
        """
        )

        await conn.close()

        return {
            "total_trips": stats["total_trips"],
            "avg_duration_minutes": round(stats["avg_duration_seconds"] / 60, 2),
            "data_range": {
                "earliest": stats["earliest_trip"].isoformat(),
                "latest": stats["latest_trip"].isoformat(),
            },
            "last_updated": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}"
        )


# 🏃‍♂️ Función principal para ejecutar el servidor
if __name__ == "__main__":
    logger.info("🚀 Iniciando servidor FastAPI...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,  # En producción, usar False
    )
