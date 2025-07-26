"""
Domain Entities - Taxi Duration Predictor
Entidades del dominio siguiendo DDD (Domain Driven Design)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np


@dataclass
class Location:
    """Value Object - Representa una ubicación geográfica"""

    latitude: float
    longitude: float

    def is_valid_nyc_location(self) -> bool:
        """Valida si la ubicación está dentro de los límites de NYC"""
        return -74.3 <= self.longitude <= -73.7 and 40.5 <= self.latitude <= 40.9

    def distance_to(self, other: "Location") -> float:
        """Calcula distancia haversine a otra ubicación en km"""
        R = 6371  # Radio de la Tierra en km

        lat1, lon1 = np.radians(self.latitude), np.radians(self.longitude)
        lat2, lon2 = np.radians(other.latitude), np.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))

        return R * c


@dataclass
class TripDuration:
    """Value Object - Duración del viaje"""

    seconds: float

    @property
    def minutes(self) -> float:
        return self.seconds / 60

    @property
    def hours(self) -> float:
        return self.seconds / 3600

    def is_valid(self) -> bool:
        """Valida si la duración es realista"""
        return 30 <= self.seconds <= 21600  # Entre 30 segundos y 6 horas


@dataclass
class TaxiTrip:
    """Entidad Principal - Representa un viaje de taxi"""

    id: str
    vendor_id: int
    pickup_datetime: datetime
    dropoff_datetime: datetime
    passenger_count: int
    pickup_location: Location
    dropoff_location: Location
    store_and_fwd_flag: str
    trip_duration: TripDuration

    @property
    def pickup_hour(self) -> int:
        """Hora del pickup (0-23)"""
        return self.pickup_datetime.hour

    @property
    def pickup_day_of_week(self) -> int:
        """Día de la semana (0=Lunes, 6=Domingo)"""
        return self.pickup_datetime.weekday()

    @property
    def is_weekend(self) -> bool:
        """True si es fin de semana"""
        return self.pickup_day_of_week >= 5

    @property
    def is_rush_hour(self) -> bool:
        """True si es hora pico (7-9 AM o 5-7 PM)"""
        return (7 <= self.pickup_hour <= 9) or (17 <= self.pickup_hour <= 19)

    @property
    def trip_distance_km(self) -> float:
        """Distancia del viaje en kilómetros"""
        return self.pickup_location.distance_to(self.dropoff_location)

    def is_valid(self) -> bool:
        """Valida si el viaje es válido para entrenamiento"""
        return (
            self.pickup_location.is_valid_nyc_location()
            and self.dropoff_location.is_valid_nyc_location()
            and self.trip_duration.is_valid()
            and 1 <= self.passenger_count <= 6
            and self.trip_distance_km > 0.1  # Mínimo 100 metros
        )


@dataclass
class TripFeatures:
    """Value Object - Features calculadas para ML"""

    distance_km: float
    passenger_count: int
    vendor_id: int
    hour_of_day: int
    day_of_week: int
    month: int
    is_weekend: int
    is_rush_hour: int
    pickup_datetime: datetime

    def to_array(self) -> np.ndarray:
        """Convierte features a array numpy para ML"""
        return np.array(
            [
                self.distance_km,
                self.passenger_count,
                self.vendor_id,
                self.hour_of_day,
                self.day_of_week,
                self.month,
                self.is_weekend,
                self.is_rush_hour,
            ]
        )

    @classmethod
    def from_trip(cls, trip: "TaxiTrip") -> "TripFeatures":
        """Crea features desde un TaxiTrip"""
        pickup_location = trip.pickup_location
        dropoff_location = trip.dropoff_location
        distance_km = pickup_location.distance_to(dropoff_location)

        return cls(
            distance_km=distance_km,
            passenger_count=trip.passenger_count,
            vendor_id=trip.vendor_id,
            hour_of_day=trip.pickup_datetime.hour,
            day_of_week=trip.pickup_datetime.weekday(),
            month=trip.pickup_datetime.month,
            is_weekend=1 if trip.pickup_datetime.weekday() >= 5 else 0,
            is_rush_hour=1 if trip.pickup_datetime.hour in [7, 8, 9, 17, 18, 19] else 0,
            pickup_datetime=trip.pickup_datetime,
        )


@dataclass
class Prediction:
    """Entidad - Representa una predicción del modelo"""

    predicted_duration_minutes: float
    confidence_score: float
    model_version: str
    features_used: TripFeatures
    created_at: datetime

    @property
    def predicted_duration_seconds(self) -> float:
        return self.predicted_duration_minutes * 60

    def is_confident(self, threshold: float = 0.8) -> bool:
        """True si la predicción tiene alta confianza"""
        return self.confidence_score >= threshold
