"""
API Controller - Taxi Duration Predictor
Controlador FastAPI siguiendo hexagonal architecture
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
import logging

from ..pipeline.predict import PredictionPipeline
from ..adapters.ml.mlflow_adapter import ModelUnavailable

logger = logging.getLogger(__name__)

# Router para endpoints de predicción
prediction_router = APIRouter(prefix="/predict", tags=["predictions"])

# Router para endpoints de salud y modelo
health_router = APIRouter(prefix="/health", tags=["health"])

# Router para información del modelo
model_router = APIRouter(prefix="/model", tags=["model"])


# Schemas Pydantic
class PredictionRequest(BaseModel):
    """Schema para request de predicción"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pickup_latitude": 40.7589,
                "pickup_longitude": -73.9851,
                "dropoff_latitude": 40.6413,
                "dropoff_longitude": -73.7781,
                "passenger_count": 2,
                "vendor_id": 1,
                "pickup_datetime": "2025-01-15T14:30:00",
            }
        }
    )

    pickup_latitude: float = Field(..., ge=40.5, le=40.9, description="Latitud de pickup (NYC)")
    pickup_longitude: float = Field(..., ge=-74.3, le=-73.7, description="Longitud de pickup (NYC)")
    dropoff_latitude: float = Field(..., ge=40.5, le=40.9, description="Latitud de dropoff (NYC)")
    dropoff_longitude: float = Field(
        ..., ge=-74.3, le=-73.7, description="Longitud de dropoff (NYC)"
    )
    passenger_count: int = Field(1, ge=1, le=6, description="Número de pasajeros")
    vendor_id: int = Field(1, ge=1, le=2, description="ID del vendor (1 o 2)")
    pickup_datetime: Optional[datetime] = Field(None, description="Fecha/hora de pickup (opcional)")


class PredictionResponse(BaseModel):
    """Schema para response de predicción"""

    predicted_duration_minutes: float = Field(..., description="Duración predicha en minutos")
    confidence_score: Optional[float] = Field(
        ..., description="Confianza medida; null cuando no existe evidencia calibrada"
    )
    confidence_status: Literal["MEASURED", "NOT_AVAILABLE"] = Field(
        ..., description="Procedencia de la confianza"
    )
    distance_km: float = Field(..., description="Distancia del viaje en km")
    model_version: str = Field(..., description="Versión del modelo usado")
    features_used: Dict[str, Any] = Field(..., description="Features usadas en la predicción")
    prediction_timestamp: datetime = Field(..., description="Timestamp de la predicción")
    run_id: str = Field(..., description="Exact MLflow run used by this prediction")
    model: "ModelInfoResponse"


class HealthResponse(BaseModel):
    """Schema para health check"""

    status: str = Field(..., description="Estado del servicio")
    timestamp: datetime = Field(..., description="Timestamp del check")
    model_status: str = Field(..., description="Estado del modelo")
    version: str = Field(..., description="Versión del API")


class ModelInfoResponse(BaseModel):
    """Schema para información del modelo"""

    run_id: str = Field(..., description="Run de MLflow que contiene el artefacto")
    artifact_uri: str
    model_type: str = Field(..., description="Tipo de modelo")
    metrics_status: Literal["MEASURED", "NOT_AVAILABLE"] = Field(
        ..., description="Disponibilidad de métricas medidas"
    )
    metrics_provenance: str = Field(..., description="Procedencia de las métricas")
    rmse: Optional[float] = Field(None, description="RMSE medido")
    mae: Optional[float] = Field(None, description="MAE medido")
    r2_score: Optional[float] = Field(None, description="R² medido")
    features: List[str] = Field(..., description="Features usadas")
    created_at: datetime = Field(..., description="Fecha de creación")
    provenance: Optional[Dict[str, Any]] = None
    selection_status: Literal["ELIGIBLE", "LEGACY_OR_INVALID"]


# Global pipeline instance
_prediction_pipeline: Optional[PredictionPipeline] = None


# Dependency para obtener pipeline de predicción
async def get_prediction_pipeline() -> PredictionPipeline:
    """Dependency para inyectar pipeline de predicción (singleton)"""
    global _prediction_pipeline
    if _prediction_pipeline is None:
        logger.info("Inicializando PredictionPipeline...")
        try:
            _prediction_pipeline = PredictionPipeline()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Model store is unavailable") from exc
        logger.info("PredictionPipeline inicializado correctamente")
    return _prediction_pipeline


# Endpoints de predicción
@prediction_router.post("/", response_model=PredictionResponse)
async def predict_trip_duration(
    request: PredictionRequest,
    pipeline: PredictionPipeline = Depends(get_prediction_pipeline),
):
    """
    Predice la duración de un viaje de taxi

    - **pickup_latitude**: Latitud de origen (40.5-40.9 para NYC)
    - **pickup_longitude**: Longitud de origen (-74.3 a -73.7 para NYC)
    - **dropoff_latitude**: Latitud de destino (40.5-40.9 para NYC)
    - **dropoff_longitude**: Longitud de destino (-74.3 a -73.7 para NYC)
    - **passenger_count**: Número de pasajeros (1-6)
    - **vendor_id**: ID del vendor (1 o 2)
    - **pickup_datetime**: Fecha/hora de pickup (opcional, default: ahora)
    """
    try:
        # Realizar predicción
        prediction = await pipeline.predict_trip_duration(
            pickup_lat=request.pickup_latitude,
            pickup_lon=request.pickup_longitude,
            dropoff_lat=request.dropoff_latitude,
            dropoff_lon=request.dropoff_longitude,
            passenger_count=request.passenger_count,
            vendor_id=request.vendor_id,
            pickup_datetime=request.pickup_datetime,
        )

        if prediction is None:
            raise HTTPException(status_code=500, detail="Error interno en predicción")

        # Convertir a response schema
        return PredictionResponse(
            predicted_duration_minutes=prediction.predicted_duration_minutes,
            confidence_score=prediction.confidence_score,
            confidence_status=prediction.confidence_status,
            distance_km=prediction.features_used.distance_km,
            model_version=prediction.model_version,
            features_used={
                "distance_km": prediction.features_used.distance_km,
                "passenger_count": prediction.features_used.passenger_count,
                "vendor_id": prediction.features_used.vendor_id,
                "hour_of_day": prediction.features_used.hour_of_day,
                "day_of_week": prediction.features_used.day_of_week,
                "month": prediction.features_used.month,
                "is_weekend": prediction.features_used.is_weekend,
                "is_rush_hour": prediction.features_used.is_rush_hour,
            },
            prediction_timestamp=prediction.created_at,
            run_id=prediction.model_info["run_id"],
            model=ModelInfoResponse(**prediction.model_info),
        )

    except ModelUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error interno: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# Endpoints de salud
@health_router.get("/", response_model=HealthResponse)
async def health_check(pipeline: PredictionPipeline = Depends(get_prediction_pipeline)):
    """
    Verifica la salud del servicio y el estado del modelo
    """
    try:
        # Verificar estado del modelo
        model_status = await pipeline.get_model_status()

        return HealthResponse(
            status="healthy" if model_status["status"] == "ready" else "degraded",
            timestamp=datetime.now(),
            model_status=model_status["status"],
            version="1.0.0",
        )

    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            model_status="error",
            version="1.0.0",
        )


@health_router.get("/model", response_model=ModelInfoResponse)
async def model_info(pipeline: PredictionPipeline = Depends(get_prediction_pipeline)):
    """
    Obtiene información del modelo disponible en el tracking configurado
    """
    try:
        model_info = await pipeline.mlflow_adapter.get_model_info()

        if not model_info:
            raise HTTPException(status_code=404, detail="No hay modelo disponible")

        return ModelInfoResponse(**model_info)

    except ModelUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo info del modelo: {e}")
        raise HTTPException(status_code=503, detail="Model store is unavailable")


# Router principal que combina todos los endpoints
def create_api_router() -> APIRouter:
    """Crea el router principal de la API"""
    main_router = APIRouter()

    # Incluir routers
    main_router.include_router(prediction_router)
    main_router.include_router(health_router)
    main_router.include_router(model_router)

    return main_router
