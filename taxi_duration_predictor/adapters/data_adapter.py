"""
PostgreSQL Data Adapter - Taxi Duration Predictor
Implementa el puerto TripRepository usando PostgreSQL
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
import asyncpg
from sqlalchemy import create_engine, text
import numpy as np

from ..domain.entities import TaxiTrip, Location, TripDuration, Prediction
from ..domain.ports import TripRepository, PredictionRepository

logger = logging.getLogger(__name__)


class PostgreSQLTripRepository(TripRepository):
    """Adaptador PostgreSQL para el repositorio de viajes"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)

    async def _get_connection(self):
        """Obtiene conexión asyncpg"""
        return await asyncpg.connect(
            self.connection_string.replace("postgresql://", "postgresql://")
        )

    async def initialize_schema(self):
        """Crea las tablas necesarias"""
        create_tables_sql = """
        -- Tabla principal de viajes
        CREATE TABLE IF NOT EXISTS taxi_trips (
            id VARCHAR(50) PRIMARY KEY,
            vendor_id INTEGER NOT NULL,
            pickup_datetime TIMESTAMP NOT NULL,
            dropoff_datetime TIMESTAMP NOT NULL,
            passenger_count INTEGER NOT NULL,
            pickup_longitude DECIMAL(10, 7) NOT NULL,
            pickup_latitude DECIMAL(10, 7) NOT NULL,
            dropoff_longitude DECIMAL(10, 7) NOT NULL,
            dropoff_latitude DECIMAL(10, 7) NOT NULL,
            store_and_fwd_flag VARCHAR(1) NOT NULL,
            trip_duration_seconds DECIMAL(10, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Índices para optimizar consultas
            INDEX idx_pickup_datetime (pickup_datetime),
            INDEX idx_vendor_id (vendor_id),
            INDEX idx_trip_duration (trip_duration_seconds),
            INDEX idx_coordinates (pickup_longitude, pickup_latitude)
        );

        -- Tabla de predicciones
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            trip_id VARCHAR(50) NOT NULL,
            predicted_duration_seconds DECIMAL(10, 2) NOT NULL,
            confidence_score DECIMAL(5, 4) NOT NULL,
            model_version VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Features usadas para la predicción (JSON)
            features_json JSONB,

            FOREIGN KEY (trip_id) REFERENCES taxi_trips(id),
            INDEX idx_trip_id (trip_id),
            INDEX idx_created_at (created_at),
            INDEX idx_model_version (model_version)
        );
        """

        conn = await self._get_connection()
        try:
            await conn.execute(create_tables_sql)
            logger.info("✅ Esquema de base de datos inicializado")
        finally:
            await conn.close()

    async def save_trip(self, trip: TaxiTrip) -> bool:
        """Guarda un viaje en PostgreSQL"""
        try:
            conn = await self._get_connection()
            try:
                await conn.execute(
                    """
                    INSERT INTO taxi_trips (
                        id, vendor_id, pickup_datetime, dropoff_datetime,
                        passenger_count, pickup_longitude, pickup_latitude,
                        dropoff_longitude, dropoff_latitude, store_and_fwd_flag,
                        trip_duration_seconds
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (id) DO UPDATE SET
                        vendor_id = EXCLUDED.vendor_id,
                        pickup_datetime = EXCLUDED.pickup_datetime,
                        dropoff_datetime = EXCLUDED.dropoff_datetime,
                        passenger_count = EXCLUDED.passenger_count,
                        pickup_longitude = EXCLUDED.pickup_longitude,
                        pickup_latitude = EXCLUDED.pickup_latitude,
                        dropoff_longitude = EXCLUDED.dropoff_longitude,
                        dropoff_latitude = EXCLUDED.dropoff_latitude,
                        store_and_fwd_flag = EXCLUDED.store_and_fwd_flag,
                        trip_duration_seconds = EXCLUDED.trip_duration_seconds
                """,
                    trip.id,
                    trip.vendor_id,
                    trip.pickup_datetime,
                    trip.dropoff_datetime,
                    trip.passenger_count,
                    trip.pickup_location.longitude,
                    trip.pickup_location.latitude,
                    trip.dropoff_location.longitude,
                    trip.dropoff_location.latitude,
                    trip.store_and_fwd_flag,
                    trip.trip_duration.seconds,
                )
                return True
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error guardando viaje {trip.id}: {e}")
            return False

    async def get_trip_by_id(self, trip_id: str) -> Optional[TaxiTrip]:
        """Obtiene un viaje por su ID"""
        try:
            conn = await self._get_connection()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM taxi_trips WHERE id = $1
                """,
                    trip_id,
                )

                if row:
                    return self._row_to_trip(row)
                return None
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error obteniendo viaje {trip_id}: {e}")
            return None

    async def get_trips_for_training(
        self, limit: Optional[int] = None
    ) -> List[TaxiTrip]:
        """Obtiene viajes válidos para entrenamiento"""
        try:
            conn = await self._get_connection()
            try:
                query = """
                    SELECT * FROM taxi_trips
                    WHERE trip_duration_seconds BETWEEN 30 AND 21600  -- 30 segundos a 6 horas
                    AND passenger_count BETWEEN 1 AND 6
                    AND pickup_longitude BETWEEN -74.3 AND -73.7
                    AND pickup_latitude BETWEEN 40.5 AND 40.9
                    AND dropoff_longitude BETWEEN -74.3 AND -73.7
                    AND dropoff_latitude BETWEEN 40.5 AND 40.9
                    ORDER BY pickup_datetime
                """

                if limit:
                    query += f" LIMIT {limit}"

                rows = await conn.fetch(query)
                return [self._row_to_trip(row) for row in rows]
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error obteniendo viajes para entrenamiento: {e}")
            return []

    async def get_trips_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[TaxiTrip]:
        """Obtiene viajes en un rango de fechas"""
        try:
            conn = await self._get_connection()
            try:
                rows = await conn.fetch(
                    """
                    SELECT * FROM taxi_trips
                    WHERE pickup_datetime BETWEEN $1 AND $2
                    ORDER BY pickup_datetime
                """,
                    start_date,
                    end_date,
                )

                return [self._row_to_trip(row) for row in rows]
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error obteniendo viajes por fecha: {e}")
            return []

    async def bulk_insert_trips(self, trips: List[TaxiTrip]) -> int:
        """Inserta múltiples viajes de forma eficiente"""
        if not trips:
            return 0

        try:
            conn = await self._get_connection()
            try:
                # Preparar datos para inserción en lote
                trip_data = [
                    (
                        trip.id,
                        trip.vendor_id,
                        trip.pickup_datetime,
                        trip.dropoff_datetime,
                        trip.passenger_count,
                        trip.pickup_location.longitude,
                        trip.pickup_location.latitude,
                        trip.dropoff_location.longitude,
                        trip.dropoff_location.latitude,
                        trip.store_and_fwd_flag,
                        trip.trip_duration.seconds,
                    )
                    for trip in trips
                ]

                # Inserción en lote usando copy
                await conn.executemany(
                    """
                    INSERT INTO taxi_trips (
                        id, vendor_id, pickup_datetime, dropoff_datetime,
                        passenger_count, pickup_longitude, pickup_latitude,
                        dropoff_longitude, dropoff_latitude, store_and_fwd_flag,
                        trip_duration_seconds
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (id) DO NOTHING
                """,
                    trip_data,
                )

                logger.info(f"✅ Insertados {len(trips)} viajes en lote")
                return len(trips)

            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error en inserción en lote: {e}")
            return 0

    def _row_to_trip(self, row) -> TaxiTrip:
        """Convierte una fila de DB a entidad TaxiTrip"""
        return TaxiTrip(
            id=row["id"],
            vendor_id=row["vendor_id"],
            pickup_datetime=row["pickup_datetime"],
            dropoff_datetime=row["dropoff_datetime"],
            passenger_count=row["passenger_count"],
            pickup_location=Location(
                latitude=float(row["pickup_latitude"]),
                longitude=float(row["pickup_longitude"]),
            ),
            dropoff_location=Location(
                latitude=float(row["dropoff_latitude"]),
                longitude=float(row["dropoff_longitude"]),
            ),
            store_and_fwd_flag=row["store_and_fwd_flag"],
            trip_duration=TripDuration(seconds=float(row["trip_duration_seconds"])),
        )

    async def get_database_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la base de datos"""
        try:
            conn = await self._get_connection()
            try:
                stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_trips,
                        MIN(pickup_datetime) as earliest_trip,
                        MAX(pickup_datetime) as latest_trip,
                        AVG(trip_duration_seconds) as avg_duration_seconds,
                        AVG(passenger_count) as avg_passengers
                    FROM taxi_trips
                """
                )

                return dict(stats) if stats else {}
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}


class CSVDataLoader:
    """Utilidad para cargar datos desde CSV a PostgreSQL"""

    def __init__(self, repository: PostgreSQLTripRepository):
        self.repository = repository

    async def load_csv_to_database(self, csv_path: str, batch_size: int = 1000) -> int:
        """Carga datos desde CSV a PostgreSQL en lotes"""
        logger.info(f"🔄 Iniciando carga de {csv_path}")

        try:
            # Leer CSV en chunks para manejar archivos grandes
            total_loaded = 0

            for chunk_df in pd.read_csv(csv_path, chunksize=batch_size):
                # Convertir chunk a entidades TaxiTrip
                trips = []

                for _, row in chunk_df.iterrows():
                    try:
                        trip = self._row_to_trip_entity(row)
                        if trip and trip.is_valid():
                            trips.append(trip)
                    except Exception as e:
                        logger.warning(f"Error procesando fila: {e}")
                        continue

                # Insertar lote
                if trips:
                    loaded = await self.repository.bulk_insert_trips(trips)
                    total_loaded += loaded
                    logger.info(f"📊 Cargadas {total_loaded} filas hasta ahora...")

            logger.info(f"✅ Carga completa: {total_loaded} viajes")
            return total_loaded

        except Exception as e:
            logger.error(f"Error cargando CSV: {e}")
            return 0

    def _row_to_trip_entity(self, row) -> Optional[TaxiTrip]:
        """Convierte una fila de CSV a entidad TaxiTrip"""
        try:
            return TaxiTrip(
                id=str(row["id"]),
                vendor_id=int(row["vendor_id"]),
                pickup_datetime=pd.to_datetime(row["pickup_datetime"]),
                dropoff_datetime=pd.to_datetime(row["dropoff_datetime"]),
                passenger_count=int(row["passenger_count"]),
                pickup_location=Location(
                    latitude=float(row["pickup_latitude"]),
                    longitude=float(row["pickup_longitude"]),
                ),
                dropoff_location=Location(
                    latitude=float(row["dropoff_latitude"]),
                    longitude=float(row["dropoff_longitude"]),
                ),
                store_and_fwd_flag=str(row["store_and_fwd_flag"]),
                trip_duration=TripDuration(seconds=float(row["trip_duration"])),
            )
        except Exception as e:
            logger.error(f"Error creando TaxiTrip desde fila: {e}")
            return None
