"""
Prediction Pipeline - Taxi Duration Predictor
Script para realizar predicciones usando modelos entrenados
"""

import asyncio
import sys
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ..adapters.ml.mlflow_adapter import MLflowAdapter
from ..domain.entities import TripFeatures, Location, Prediction
from ..domain.services import TripPredictionService

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PredictionPipeline:
    """Pipeline de predicción de duración de viajes"""

    def __init__(self, mlflow_config: Dict[str, str] = None):
        """
        Args:
            mlflow_config: Configuración de MLflow
        """
        # Configurar MLflow
        mlflow_config = mlflow_config or {
            "tracking_uri": "sqlite:///data/mlflow.db",
            "experiment_name": "taxi_duration_prediction",
        }
        self.mlflow_adapter = MLflowAdapter(**mlflow_config)

        # Handle prediction logic directly in the pipeline
        # Domain service is not needed for current implementation
        logger.info("PredictionPipeline inicializado correctamente")

    async def predict_trip_duration(
        self,
        pickup_lat: float,
        pickup_lon: float,
        dropoff_lat: float,
        dropoff_lon: float,
        passenger_count: int = 1,
        vendor_id: int = 1,
        pickup_datetime: datetime = None,
    ) -> Optional[Prediction]:
        """
        Predice la duración de un viaje de taxi

        Args:
            pickup_lat: Latitud de origen
            pickup_lon: Longitud de origen
            dropoff_lat: Latitud de destino
            dropoff_lon: Longitud de destino
            passenger_count: Número de pasajeros
            vendor_id: ID del vendor
            pickup_datetime: Fecha/hora de pickup (default: ahora)

        Returns:
            Prediction object con la predicción
        """
        try:
            # Usar tiempo actual si no se especifica
            if pickup_datetime is None:
                pickup_datetime = datetime.now()

            # Crear entidades de dominio
            pickup_location = Location(latitude=pickup_lat, longitude=pickup_lon)
            dropoff_location = Location(latitude=dropoff_lat, longitude=dropoff_lon)

            # Validar ubicaciones (NYC)
            if not pickup_location.is_valid_nyc_location():
                raise ValueError(
                    f"Ubicación de pickup inválida: {pickup_lat}, {pickup_lon}"
                )

            if not dropoff_location.is_valid_nyc_location():
                raise ValueError(
                    f"Ubicación de dropoff inválida: {dropoff_lat}, {dropoff_lon}"
                )

            # Calcular distancia
            distance_km = pickup_location.distance_to(dropoff_location)

            # Crear features
            features = TripFeatures(
                distance_km=distance_km,
                passenger_count=passenger_count,
                vendor_id=vendor_id,
                hour_of_day=pickup_datetime.hour,
                day_of_week=pickup_datetime.weekday(),
                month=pickup_datetime.month,
                is_weekend=1 if pickup_datetime.weekday() >= 5 else 0,
                is_rush_hour=1 if pickup_datetime.hour in [7, 8, 9, 17, 18, 19] else 0,
                pickup_datetime=pickup_datetime,
            )

            # Realizar predicción directamente usando MLflow
            try:
                # Get the best model
                model = await self.mlflow_adapter.load_best_model()
                if not model:
                    logger.error("No se encontró modelo disponible")
                    return None

                # Prepare features for prediction
                feature_dict = {
                    "distance_km": features.distance_km,
                    "passenger_count": features.passenger_count,
                    "vendor_id": features.vendor_id,
                    "hour_of_day": features.hour_of_day,
                    "day_of_week": features.day_of_week,
                    "month": features.month,
                    "is_weekend": features.is_weekend,
                    "is_rush_hour": features.is_rush_hour,
                }

                # Make prediction
                import pandas as pd

                feature_df = pd.DataFrame([feature_dict])
                prediction_result = model.predict(feature_df)[0]

                # Create prediction object
                prediction = Prediction(
                    predicted_duration_minutes=float(prediction_result),
                    confidence_score=0.8,  # Default confidence
                    model_version="latest",
                    features_used=features,
                    created_at=datetime.now(),
                )

            except Exception as model_error:
                logger.error(f"Error en predicción con modelo: {model_error}")
                # Fallback to simple heuristic
                estimated_duration = features.distance_km * 3.5  # ~3.5 minutes per km
                prediction = Prediction(
                    predicted_duration_minutes=estimated_duration,
                    confidence_score=0.5,  # Lower confidence for fallback
                    model_version="fallback",
                    features_used=features,
                    created_at=datetime.now(),
                )

            logger.info(
                f"Predicción realizada: {prediction.predicted_duration_minutes:.1f} minutos"
            )

            return prediction

        except Exception as e:
            logger.error(f"Error en predicción: {e}")
            return None

    async def predict(
        self, prediction_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Convenient predict method that matches FastAPI interface

        Args:
            prediction_data: Dictionary containing prediction request data

        Returns:
            Dictionary with prediction results or None if failed
        """
        try:
            # Parse pickup_datetime
            pickup_datetime = None
            if "pickup_datetime" in prediction_data:
                from datetime import datetime

                pickup_datetime_str = prediction_data["pickup_datetime"]
                if isinstance(pickup_datetime_str, str):
                    pickup_datetime = datetime.fromisoformat(
                        pickup_datetime_str.replace("Z", "+00:00")
                    )
                else:
                    pickup_datetime = pickup_datetime_str

            # Call the main prediction method
            prediction = await self.predict_trip_duration(
                pickup_lat=prediction_data["pickup_latitude"],
                pickup_lon=prediction_data["pickup_longitude"],
                dropoff_lat=prediction_data["dropoff_latitude"],
                dropoff_lon=prediction_data["dropoff_longitude"],
                passenger_count=prediction_data.get("passenger_count", 1),
                vendor_id=prediction_data.get("vendor_id", 1),
                pickup_datetime=pickup_datetime,
            )

            if prediction:
                # Convert to API response format
                return {
                    "predicted_duration_minutes": prediction.predicted_duration_minutes,
                    "confidence_score": prediction.confidence_score,
                    "model_version": prediction.model_version,
                    "features_used": {
                        "distance_km": prediction.features_used.distance_km,
                        "passenger_count": prediction.features_used.passenger_count,
                        "vendor_id": prediction.features_used.vendor_id,
                        "hour_of_day": prediction.features_used.hour_of_day,
                        "day_of_week": prediction.features_used.day_of_week,
                        "month": prediction.features_used.month,
                        "is_weekend": bool(prediction.features_used.is_weekend),
                        "is_rush_hour": bool(prediction.features_used.is_rush_hour),
                    },
                    "created_at": prediction.created_at.isoformat(),
                }
            else:
                return None

        except Exception as e:
            logger.error(f"Error en método predict: {e}")
            return None

    async def batch_predict(self, trips_data: list) -> list:
        """
        Realiza predicciones en lote

        Args:
            trips_data: Lista de diccionarios con datos de viajes

        Returns:
            Lista de predicciones
        """
        predictions = []

        logger.info(f"Iniciando predicciones en lote para {len(trips_data)} viajes...")

        for i, trip in enumerate(trips_data, 1):
            try:
                prediction = await self.predict_trip_duration(
                    pickup_lat=trip["pickup_lat"],
                    pickup_lon=trip["pickup_lon"],
                    dropoff_lat=trip["dropoff_lat"],
                    dropoff_lon=trip["dropoff_lon"],
                    passenger_count=trip.get("passenger_count", 1),
                    vendor_id=trip.get("vendor_id", 1),
                    pickup_datetime=trip.get("pickup_datetime"),
                )

                predictions.append(prediction)

                if i % 100 == 0:  # Log cada 100 predicciones
                    logger.info(f"Predicciones completadas: {i}/{len(trips_data)}")

            except Exception as e:
                logger.error(f"Error en predicción {i}: {e}")
                predictions.append(None)

        successful_predictions = sum(1 for p in predictions if p is not None)
        logger.info(
            f"Predicciones completadas: {successful_predictions}/{len(trips_data)}"
        )

        return predictions

    async def get_model_status(self) -> Dict[str, Any]:
        """Obtiene el estado del modelo en producción"""
        try:
            model_info = await self.mlflow_adapter.get_model_info()

            if not model_info:
                return {"status": "no_model", "message": "No hay modelo disponible"}

            # Verificar si el modelo se puede cargar
            model = await self.mlflow_adapter.load_best_model()

            if model is None:
                return {"status": "error", "message": "No se puede cargar el modelo"}

            return {
                "status": "ready",
                "message": "Modelo listo para predicciones",
                "model_info": model_info,
            }

        except Exception as e:
            logger.error(f"Error obteniendo estado del modelo: {e}")
            return {"status": "error", "message": str(e)}

    async def validate_prediction_input(self, data: dict) -> Dict[str, Any]:
        """Valida datos de entrada para predicción"""
        errors = []

        # Validar campos requeridos
        required_fields = ["pickup_lat", "pickup_lon", "dropoff_lat", "dropoff_lon"]

        for field in required_fields:
            if field not in data:
                errors.append(f"Campo requerido faltante: {field}")
            elif not isinstance(data[field], (int, float)):
                errors.append(f"Campo {field} debe ser numérico")

        # Validar rangos de coordenadas NYC
        if "pickup_lat" in data and "pickup_lon" in data:
            pickup_location = Location(data["pickup_lat"], data["pickup_lon"])
            if not pickup_location.is_valid_nyc_location():
                errors.append("Ubicación de pickup fuera de NYC")

        if "dropoff_lat" in data and "dropoff_lon" in data:
            dropoff_location = Location(data["dropoff_lat"], data["dropoff_lon"])
            if not dropoff_location.is_valid_nyc_location():
                errors.append("Ubicación de dropoff fuera de NYC")

        # Validar campos opcionales
        if "passenger_count" in data:
            if (
                not isinstance(data["passenger_count"], int)
                or data["passenger_count"] < 1
                or data["passenger_count"] > 6
            ):
                errors.append("passenger_count debe ser un entero entre 1 y 6")

        if "vendor_id" in data:
            if not isinstance(data["vendor_id"], int) or data["vendor_id"] not in [
                1,
                2,
            ]:
                errors.append("vendor_id debe ser 1 o 2")

        return {"valid": len(errors) == 0, "errors": errors}


async def predict_single_trip():
    """Ejemplo de predicción individual"""
    pipeline = PredictionPipeline()

    # Ejemplo: Times Square a JFK Airport
    prediction = await pipeline.predict_trip_duration(
        pickup_lat=40.7589,
        pickup_lon=-73.9851,  # Times Square
        dropoff_lat=40.6413,
        dropoff_lon=-73.7781,  # JFK Airport
        passenger_count=2,
        vendor_id=1,
    )

    if prediction:
        print(
            f"🚕 Predicción de duración: {prediction.predicted_duration_minutes:.1f} minutos"
        )
        print(f"   Confianza: {prediction.confidence_score:.2f}")
        print(f"   Distancia: {prediction.features_used.distance_km:.1f} km")
    else:
        print("❌ Error en predicción")


async def main():
    """Función principal de ejemplo"""
    pipeline = PredictionPipeline()

    # Verificar estado del modelo
    status = await pipeline.get_model_status()
    print(f"Estado del modelo: {status}")

    if status["status"] == "ready":
        # Realizar predicción de ejemplo
        await predict_single_trip()
    else:
        print("Modelo no está listo para predicciones")


if __name__ == "__main__":
    asyncio.run(main())
