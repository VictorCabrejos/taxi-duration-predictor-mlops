"""
Domain Ports - Taxi Duration Predictor
Interfaces (Puertos) para la arquitectura hexagonal
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from .entities import TaxiTrip, TripFeatures, Prediction


class TripRepository(ABC):
    """Puerto - Repositorio de viajes de taxi"""

    @abstractmethod
    async def save_trip(self, trip: TaxiTrip) -> bool:
        """Guarda un viaje en el repositorio"""
        pass

    @abstractmethod
    async def get_trip_by_id(self, trip_id: str) -> Optional[TaxiTrip]:
        """Obtiene un viaje por su ID"""
        pass

    @abstractmethod
    async def get_trips_for_training(
        self, limit: Optional[int] = None
    ) -> List[TaxiTrip]:
        """Obtiene viajes válidos para entrenamiento"""
        pass

    @abstractmethod
    async def get_trips_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[TaxiTrip]:
        """Obtiene viajes en un rango de fechas"""
        pass

    @abstractmethod
    async def bulk_insert_trips(self, trips: List[TaxiTrip]) -> int:
        """Inserta múltiples viajes de forma eficiente"""
        pass


class PredictionRepository(ABC):
    """Puerto - Repositorio de predicciones"""

    @abstractmethod
    async def save_prediction(self, prediction: Prediction) -> bool:
        """Guarda una predicción"""
        pass

    @abstractmethod
    async def get_predictions_by_trip_id(self, trip_id: str) -> List[Prediction]:
        """Obtiene predicciones para un viaje específico"""
        pass

    @abstractmethod
    async def get_recent_predictions(self, limit: int = 100) -> List[Prediction]:
        """Obtiene las predicciones más recientes"""
        pass


class MLModelService(ABC):
    """Puerto - Servicio de Machine Learning"""

    @abstractmethod
    async def train_model(self, trips: List[TaxiTrip]) -> Dict[str, Any]:
        """Entrena un nuevo modelo con los viajes proporcionados"""
        pass

    @abstractmethod
    async def predict_duration(self, features: TripFeatures) -> Prediction:
        """Predice la duración de un viaje"""
        pass

    @abstractmethod
    async def evaluate_model(self, test_trips: List[TaxiTrip]) -> Dict[str, float]:
        """Evalúa el modelo actual con datos de prueba"""
        pass

    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Obtiene información del modelo actual"""
        pass

    @abstractmethod
    async def load_model(self, model_version: str) -> bool:
        """Carga una versión específica del modelo"""
        pass


class FeatureEngineering(ABC):
    """Puerto - Servicio de Feature Engineering"""

    @abstractmethod
    def extract_features(self, trip: TaxiTrip) -> TripFeatures:
        """Extrae features de un viaje"""
        pass

    @abstractmethod
    def validate_features(self, features: TripFeatures) -> bool:
        """Valida que las features sean válidas"""
        pass

    @abstractmethod
    def normalize_features(self, features: List[TripFeatures]) -> List[TripFeatures]:
        """Normaliza un conjunto de features"""
        pass


class NotificationService(ABC):
    """Puerto - Servicio de notificaciones"""

    @abstractmethod
    async def notify_training_complete(self, model_metrics: Dict[str, float]) -> None:
        """Notifica que el entrenamiento se completó"""
        pass

    @abstractmethod
    async def notify_prediction_error(self, error: str, trip_id: str) -> None:
        """Notifica un error en predicción"""
        pass

    @abstractmethod
    async def notify_model_drift(self, drift_metrics: Dict[str, float]) -> None:
        """Notifica drift del modelo"""
        pass


class MetricsService(ABC):
    """Puerto - Servicio de métricas y monitoreo"""

    @abstractmethod
    async def log_prediction_time(self, duration_ms: float) -> None:
        """Registra tiempo de predicción"""
        pass

    @abstractmethod
    async def log_model_accuracy(self, accuracy: float) -> None:
        """Registra accuracy del modelo"""
        pass

    @abstractmethod
    async def get_system_health(self) -> Dict[str, Any]:
        """Obtiene estado de salud del sistema"""
        pass

    @abstractmethod
    async def get_prediction_stats(self, days: int = 7) -> Dict[str, Any]:
        """Obtiene estadísticas de predicciones"""
        pass
