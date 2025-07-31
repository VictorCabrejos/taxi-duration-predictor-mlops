"""
Domain Services - Taxi Duration Predictor
Servicios del dominio (Business Logic)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .entities import TaxiTrip, TripFeatures, Prediction
from .ports import (
    TripRepository,
    PredictionRepository,
    MLModelService,
    FeatureEngineering,
    NotificationService,
    MetricsService,
)

logger = logging.getLogger(__name__)


class TripPredictionService:
    """Servicio principal - Orquesta la predicción de viajes"""

    def __init__(
        self,
        trip_repo: TripRepository,
        prediction_repo: PredictionRepository,
        ml_service: MLModelService,
        feature_service: FeatureEngineering,
        metrics_service: MetricsService,
        notification_service: NotificationService,
    ):
        self.trip_repo = trip_repo
        self.prediction_repo = prediction_repo
        self.ml_service = ml_service
        self.feature_service = feature_service
        self.metrics_service = metrics_service
        self.notification_service = notification_service

    async def predict_trip_duration(self, trip: TaxiTrip) -> Prediction:
        """
        Caso de uso principal: Predecir duración de un viaje
        """
        start_time = datetime.now()

        try:
            # 1. Validar que el viaje sea válido
            if not trip.is_valid():
                raise ValueError(f"Viaje inválido: {trip.id}")

            # 2. Extraer features
            features = self.feature_service.extract_features(trip)

            # 3. Validar features
            if not self.feature_service.validate_features(features):
                raise ValueError(f"Features inválidas para viaje: {trip.id}")

            # 4. Realizar predicción
            prediction = await self.ml_service.predict_duration(features)

            # 5. Guardar predicción
            await self.prediction_repo.save_prediction(prediction)

            # 6. Registrar métricas
            prediction_time = (datetime.now() - start_time).total_seconds() * 1000
            await self.metrics_service.log_prediction_time(prediction_time)

            logger.info(
                f"Predicción exitosa para viaje {trip.id}: {prediction.predicted_duration_minutes:.1f} min"
            )

            return prediction

        except Exception as e:
            # Notificar error
            await self.notification_service.notify_prediction_error(str(e), trip.id)
            logger.error(f"Error prediciendo viaje {trip.id}: {e}")
            raise


class ModelTrainingService:
    """Servicio - Entrenamiento de modelos"""

    def __init__(
        self,
        trip_repo: TripRepository,
        ml_service: MLModelService,
        feature_service: FeatureEngineering,
        metrics_service: MetricsService,
        notification_service: NotificationService,
    ):
        self.trip_repo = trip_repo
        self.ml_service = ml_service
        self.feature_service = feature_service
        self.metrics_service = metrics_service
        self.notification_service = notification_service

    async def train_new_model(self, max_trips: Optional[int] = None) -> Dict[str, Any]:
        """
        Caso de uso: Entrenar un nuevo modelo
        """
        logger.info("Iniciando entrenamiento de modelo...")

        try:
            # 1. Obtener datos de entrenamiento
            trips = await self.trip_repo.get_trips_for_training(limit=max_trips)
            logger.info(f"Obtenidos {len(trips)} viajes para entrenamiento")

            if len(trips) < 1000:
                raise ValueError(
                    "Insuficientes datos para entrenamiento (mínimo 1000 viajes)"
                )

            # 2. Validar calidad de datos
            valid_trips = [trip for trip in trips if trip.is_valid()]
            logger.info(f"Viajes válidos: {len(valid_trips)} / {len(trips)}")

            if len(valid_trips) < len(trips) * 0.8:
                logger.warning("Más del 20% de viajes inválidos")

            # 3. Entrenar modelo
            training_result = await self.ml_service.train_model(valid_trips)

            # 4. Registrar métricas
            if "accuracy" in training_result:
                await self.metrics_service.log_model_accuracy(
                    training_result["accuracy"]
                )

            # 5. Notificar entrenamiento completado
            await self.notification_service.notify_training_complete(training_result)

            logger.info(f"Entrenamiento completado: {training_result}")

            return training_result

        except Exception as e:
            logger.error(f"Error en entrenamiento: {e}")
            raise


class DataValidationService:
    """Servicio - Validación y limpieza de datos"""

    def __init__(self, trip_repo: TripRepository):
        self.trip_repo = trip_repo

    async def validate_and_clean_trip(
        self, raw_trip_data: Dict[str, Any]
    ) -> Optional[TaxiTrip]:
        """
        Valida y limpia datos de un viaje crudo
        """
        try:
            # Crear entidad TaxiTrip desde datos crudos
            trip = self._create_trip_from_raw_data(raw_trip_data)

            # Validar
            if trip.is_valid():
                return trip
            else:
                logger.warning(f"Viaje inválido descartado: {trip.id}")
                return None

        except Exception as e:
            logger.error(f"Error procesando viaje: {e}")
            return None

    def _create_trip_from_raw_data(self, data: Dict[str, Any]) -> TaxiTrip:
        """Convierte datos crudos a entidad TaxiTrip"""
        from .entities import Location, TripDuration

        return TaxiTrip(
            id=data["id"],
            vendor_id=int(data["vendor_id"]),
            pickup_datetime=data["pickup_datetime"],
            dropoff_datetime=data["dropoff_datetime"],
            passenger_count=int(data["passenger_count"]),
            pickup_location=Location(
                latitude=float(data["pickup_latitude"]),
                longitude=float(data["pickup_longitude"]),
            ),
            dropoff_location=Location(
                latitude=float(data["dropoff_latitude"]),
                longitude=float(data["dropoff_longitude"]),
            ),
            store_and_fwd_flag=data["store_and_fwd_flag"],
            trip_duration=TripDuration(seconds=float(data["trip_duration"])),
        )


class MonitoringService:
    """Servicio - Monitoreo del modelo en producción"""

    def __init__(
        self,
        prediction_repo: PredictionRepository,
        ml_service: MLModelService,
        metrics_service: MetricsService,
        notification_service: NotificationService,
    ):
        self.prediction_repo = prediction_repo
        self.ml_service = ml_service
        self.metrics_service = metrics_service
        self.notification_service = notification_service

    async def check_model_performance(self, days: int = 7) -> Dict[str, Any]:
        """
        Revisa el performance del modelo en los últimos días
        """
        try:
            # Obtener estadísticas de predicciones
            stats = await self.metrics_service.get_prediction_stats(days)

            # Obtener información del modelo actual
            model_info = await self.ml_service.get_model_info()

            # Detectar posible drift
            if self._detect_model_drift(stats):
                await self.notification_service.notify_model_drift(stats)

            return {
                "prediction_stats": stats,
                "model_info": model_info,
                "health_status": (
                    "healthy" if stats.get("avg_confidence", 0) > 0.7 else "degraded"
                ),
            }

        except Exception as e:
            logger.error(f"Error monitoreando modelo: {e}")
            return {"health_status": "error", "error": str(e)}

    def _detect_model_drift(self, stats: Dict[str, Any]) -> bool:
        """Detecta drift simple basado en confianza promedio"""
        avg_confidence = stats.get("avg_confidence", 1.0)
        return avg_confidence < 0.6  # Threshold configurable
