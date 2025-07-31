"""
Training Pipeline - Taxi Duration Predictor
Script de entrenamiento para modelos ML con MLflow tracking
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict, Any

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ..adapters.database.data_adapter import PostgreSQLAdapter
from ..adapters.ml.sklearn_adapter import SklearnModelsAdapter
from ..adapters.ml.mlflow_adapter import MLflowAdapter
from ..domain.services import TripPredictionService, ModelTrainingService

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TrainingPipeline:
    """Pipeline completo de entrenamiento de modelos"""

    def __init__(
        self,
        connection_string: str,
        mlflow_config: Dict[str, str] = None,
        sample_size: int = 10000,
    ):
        """
        Args:
            connection_string: PostgreSQL connection string
            mlflow_config: Configuración de MLflow
            sample_size: Tamaño de muestra para entrenamiento
        """
        self.connection_string = connection_string
        self.sample_size = sample_size

        # Inicializar adapters
        self.data_adapter = PostgreSQLAdapter(connection_string)
        self.ml_adapter = SklearnModelsAdapter()

        # Configurar MLflow
        mlflow_config = mlflow_config or {
            "tracking_uri": "sqlite:///data/mlflow.db",
            "experiment_name": "taxi_duration_prediction",
        }
        self.mlflow_adapter = MLflowAdapter(**mlflow_config)

        # Handle training logic directly in the pipeline
        logger.info("TrainingPipeline inicializado correctamente")
        self.domain_service = None

    async def extract_training_data(self) -> tuple:
        """Extrae datos de entrenamiento desde la base de datos"""
        logger.info(f"Extrayendo {self.sample_size} registros para entrenamiento...")

        try:
            # Obtener datos crudos
            trips = await self.data_adapter.get_trips_for_training(
                limit=self.sample_size
            )

            if not trips:
                raise ValueError("No se encontraron datos de entrenamiento")

            # Convertir a DataFrame para feature engineering
            import pandas as pd

            df_data = []
            for trip in trips:
                df_data.append(
                    {
                        "pickup_longitude": trip.pickup_location.longitude,
                        "pickup_latitude": trip.pickup_location.latitude,
                        "dropoff_longitude": trip.dropoff_location.longitude,
                        "dropoff_latitude": trip.dropoff_location.latitude,
                        "passenger_count": trip.passenger_count,
                        "vendor_id": trip.vendor_id,
                        "pickup_datetime": trip.pickup_datetime,
                        "trip_duration_seconds": trip.trip_duration.seconds,
                    }
                )

            df = pd.DataFrame(df_data)
            logger.info(f"Datos extraídos: {df.shape}")

            # Feature engineering
            X, y = await self.ml_adapter.prepare_features(df)

            logger.info(f"Features preparadas: X={X.shape}, y={y.shape}")
            logger.info(f"Features: {list(X.columns)}")
            logger.info(
                f"Target stats - Media: {y.mean():.1f}min, Std: {y.std():.1f}min"
            )

            return X, y

        except Exception as e:
            logger.error(f"Error extrayendo datos: {e}")
            raise

    async def train_all_models(self, X, y) -> List[Dict[str, Any]]:
        """Entrena todos los modelos disponibles"""
        logger.info("Iniciando entrenamiento de modelos...")

        try:
            # Entrenar modelos con sklearn adapter
            training_results = await self.ml_adapter.train_all_models(X, y)

            if not training_results:
                raise ValueError("No se pudieron entrenar modelos")

            # Guardar modelos en MLflow
            mlflow_results = []

            for result in training_results:
                logger.info(f"Guardando modelo {result['model_name']} en MLflow...")

                run_id = await self.mlflow_adapter.save_model(
                    model=result["model"],
                    model_name=result["model_name"],
                    metrics=result["metrics"],
                    features=result["features"],
                    hyperparams=result["hyperparams"],
                )

                result["run_id"] = run_id
                mlflow_results.append(result)

            return mlflow_results

        except Exception as e:
            logger.error(f"Error entrenando modelos: {e}")
            raise

    async def evaluate_and_select_best_model(
        self, training_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evalúa resultados y selecciona el mejor modelo"""
        logger.info("Evaluando modelos...")

        # Ordenar por RMSE (menor es mejor)
        training_results.sort(key=lambda x: x["metrics"]["rmse"])
        best_result = training_results[0]

        logger.info("\n" + "=" * 60)
        logger.info("RESUMEN DE ENTRENAMIENTO")
        logger.info("=" * 60)

        for i, result in enumerate(training_results, 1):
            metrics = result["metrics"]
            status = "🏆 MEJOR" if i == 1 else f"#{i}"

            logger.info(
                f"{status} {result['model_name']}: "
                f"RMSE={metrics['rmse']:.2f}min, "
                f"MAE={metrics['mae']:.2f}min, "
                f"R²={metrics['r2_score']:.3f}"
            )

        logger.info("=" * 60)
        logger.info(f"🏆 MODELO SELECCIONADO: {best_result['model_name']}")
        logger.info(f"   RMSE: {best_result['metrics']['rmse']:.2f} minutos")
        logger.info(f"   MAE: {best_result['metrics']['mae']:.2f} minutos")
        logger.info(f"   R²: {best_result['metrics']['r2_score']:.3f}")
        logger.info(
            f"   Tiempo entrenamiento: {best_result['metrics']['training_time_seconds']:.1f}s"
        )
        logger.info("=" * 60)

        return best_result

    async def run_complete_pipeline(self) -> Dict[str, Any]:
        """Ejecuta pipeline completo de entrenamiento"""
        start_time = datetime.now()
        logger.info(f"🚀 Iniciando pipeline de entrenamiento - {start_time}")

        try:
            # 1. Extraer datos
            X, y = await self.extract_training_data()

            # 2. Entrenar modelos
            training_results = await self.train_all_models(X, y)

            # 3. Evaluar y seleccionar mejor modelo
            best_model_result = await self.evaluate_and_select_best_model(
                training_results
            )

            # 4. Verificar que el modelo se puede cargar
            logger.info("Verificando modelo en MLflow...")
            loaded_model = await self.mlflow_adapter.load_best_model()

            if loaded_model is None:
                raise ValueError("No se pudo cargar el modelo desde MLflow")

            logger.info("✅ Modelo verificado correctamente")

            # 5. Estadísticas finales
            duration = datetime.now() - start_time

            final_stats = {
                "pipeline_duration": duration.total_seconds(),
                "models_trained": len(training_results),
                "best_model": best_model_result["model_name"],
                "best_rmse": best_model_result["metrics"]["rmse"],
                "training_samples": len(X),
                "features_count": len(X.columns),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"🎉 Pipeline completado en {duration.total_seconds():.1f}s")
            logger.info(f"   Modelos entrenados: {final_stats['models_trained']}")
            logger.info(f"   Mejor modelo: {final_stats['best_model']}")
            logger.info(f"   Mejor RMSE: {final_stats['best_rmse']:.2f} minutos")

            return final_stats

        except Exception as e:
            logger.error(f"❌ Error en pipeline: {e}")
            raise


async def main():
    """Función principal"""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Training Pipeline")
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Run bootstrap training with local data",
    )
    args = parser.parse_args()

    if args.bootstrap:
        logger.info("🤖 Ejecutando entrenamiento bootstrap...")
        return await bootstrap_training()

    # Configuración de base de datos AWS RDS
    db_config = {
        "host": "taxi-duration-db.ckj7uy651uld.us-east-1.rds.amazonaws.com",
        "port": 5432,
        "database": "postgres",
        "user": "taxiuser",
        "password": "TaxiDB2025!",
    }

    # Crear connection string para PostgreSQL
    connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

    # Configuración de MLflow
    mlflow_config = {
        "tracking_uri": "sqlite:///data/mlflow.db",
        "experiment_name": "taxi_duration_prediction",
    }

    # Crear y ejecutar pipeline
    pipeline = TrainingPipeline(
        connection_string=connection_string,
        mlflow_config=mlflow_config,
        sample_size=5000,  # Reduced for faster training
    )

    try:
        results = await pipeline.run_complete_pipeline()
        logger.info("✅ Pipeline ejecutado exitosamente")
        return results

    except Exception as e:
        logger.error(f"❌ Error ejecutando pipeline: {e}")
        raise


async def bootstrap_training():
    """Entrenamiento bootstrap con datos sintéticos"""
    try:
        import mlflow
        import mlflow.sklearn
        import pandas as pd
        import numpy as np
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import LinearRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

        logger.info("🎯 Creando datos sintéticos para bootstrap...")

        # Configurar MLflow
        mlflow.set_tracking_uri("sqlite:///data/mlflow.db")
        mlflow.set_experiment("taxi_duration_prediction")

        # Generar datos sintéticos realistas
        n_samples = 5000
        np.random.seed(42)

        # Features realistas
        data = {
            "distance_km": np.random.uniform(0.5, 50, n_samples),
            "passenger_count": np.random.choice(
                [1, 2, 3, 4, 5, 6], n_samples, p=[0.7, 0.15, 0.08, 0.04, 0.02, 0.01]
            ),
            "vendor_id": np.random.choice([1, 2], n_samples),
            "hour_of_day": np.random.randint(0, 24, n_samples),
            "day_of_week": np.random.randint(0, 7, n_samples),
            "month": np.random.randint(1, 13, n_samples),
            "is_weekend": np.random.choice([0, 1], n_samples, p=[0.71, 0.29]),
            "is_rush_hour": np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
        }

        df = pd.DataFrame(data)

        # Target realista basado en distancia + ruido
        df["duration_minutes"] = (
            5  # base time
            + df["distance_km"] * 2  # speed factor
            + df["passenger_count"] * 0.5  # loading time
            + df["is_rush_hour"] * 5  # traffic
            + np.random.normal(0, 2, n_samples)  # noise
        )

        # Ensure positive values
        df["duration_minutes"] = np.maximum(df["duration_minutes"], 1)

        logger.info(f"📊 Datos sintéticos creados: {df.shape}")
        logger.info(f"   Duración promedio: {df['duration_minutes'].mean():.1f} min")
        logger.info(f"   Distancia promedio: {df['distance_km'].mean():.1f} km")

        X = df.drop("duration_minutes", axis=1)
        y = df["duration_minutes"]

        # Modelos a entrenar
        models = [
            ("RandomForest", RandomForestRegressor(n_estimators=50, random_state=42)),
            ("LinearRegression", LinearRegression()),
        ]

        results = []

        for model_name, model in models:
            with mlflow.start_run(run_name=f"bootstrap_{model_name}"):
                logger.info(f"🔄 Entrenando {model_name}...")

                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )

                # Train model
                model.fit(X_train, y_train)

                # Predictions
                y_pred = model.predict(X_test)

                # Metrics
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)

                # Log parameters
                mlflow.log_param("model_type", model_name)
                mlflow.log_param("bootstrap", True)
                mlflow.log_param("train_size", len(X_train))
                mlflow.log_param("test_size", len(X_test))
                mlflow.log_param("synthetic_data", True)

                # Log metrics
                mlflow.log_metric("rmse", rmse)
                mlflow.log_metric("mae", mae)
                mlflow.log_metric("r2_score", r2)

                # Log model
                mlflow.sklearn.log_model(model, "model")

                results.append(
                    {"model_name": model_name, "rmse": rmse, "mae": mae, "r2": r2}
                )

                logger.info(f"✅ {model_name} completado:")
                logger.info(f"   RMSE: {rmse:.2f} min")
                logger.info(f"   MAE: {mae:.2f} min")
                logger.info(f"   R²: {r2:.3f}")

        # Find best model
        best_model = min(results, key=lambda x: x["rmse"])
        logger.info(f"🏆 Mejor modelo bootstrap: {best_model['model_name']}")
        logger.info(f"   RMSE: {best_model['rmse']:.2f} min")

        return {
            "status": "success",
            "models_trained": len(results),
            "best_model": best_model["model_name"],
            "best_rmse": best_model["rmse"],
            "synthetic_data": True,
        }

    except Exception as e:
        logger.error(f"❌ Error en entrenamiento bootstrap: {e}")
        raise


if __name__ == "__main__":
    # Ejecutar pipeline
    results = asyncio.run(main())
    print(f"\n🎯 Resultados finales: {results}")
