"""
Sklearn Models Adapter - Taxi Duration Predictor
Implementación de modelos de scikit-learn y XGBoost
"""

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
import logging
from datetime import datetime

try:
    from ...domain.ports import ModelTrainer
    from ...domain.entities import TripFeatures
except ImportError:
    # Fallback for when running outside package context
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.append(str(project_root))
    from taxi_duration_predictor.domain.ports import ModelTrainer
    from taxi_duration_predictor.domain.entities import TripFeatures

logger = logging.getLogger(__name__)


class SklearnModelsAdapter(ModelTrainer):
    """Adapter para modelos de scikit-learn y XGBoost"""

    def __init__(self):
        pass

    def get_available_models(self) -> Dict[str, Any]:
        """Retorna diccionario de modelos disponibles"""
        return {
            "RandomForest": {
                "model": RandomForestRegressor(
                    n_estimators=100, random_state=42, n_jobs=-1
                ),
                "params": {"n_estimators": 100, "random_state": 42, "n_jobs": -1},
                "requires_scaling": False,
            },
            "XGBoost": {
                "model": xgb.XGBRegressor(
                    n_estimators=100, random_state=42, verbosity=0
                ),
                "params": {"n_estimators": 100, "random_state": 42, "verbosity": 0},
                "requires_scaling": False,
            },
            "LinearRegression": {
                "model": LinearRegression(),
                "params": {},
                "requires_scaling": True,
            },
        }

    async def prepare_features(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepara features y target desde DataFrame crudo"""
        try:
            # Feature Engineering
            logger.info("Ejecutando feature engineering...")

            # 1. Distancia Haversine
            df["distance_km"] = self._calculate_haversine_distance(
                df["pickup_latitude"],
                df["pickup_longitude"],
                df["dropoff_latitude"],
                df["dropoff_longitude"],
            )

            # 2. Features temporales
            df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"])
            df["hour_of_day"] = df["pickup_datetime"].dt.hour
            df["day_of_week"] = df["pickup_datetime"].dt.dayofweek
            df["month"] = df["pickup_datetime"].dt.month

            # 3. Features categóricas
            df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
            df["is_rush_hour"] = (
                df["hour_of_day"].isin([7, 8, 9, 17, 18, 19]).astype(int)
            )

            # 4. Target (convertir a minutos)
            df["duration_minutes"] = df["trip_duration_seconds"] / 60

            # Seleccionar features finales
            feature_columns = [
                "distance_km",
                "passenger_count",
                "vendor_id",
                "hour_of_day",
                "day_of_week",
                "month",
                "is_weekend",
                "is_rush_hour",
            ]

            X = df[feature_columns]
            y = df["duration_minutes"]

            # Validar datos
            X = X.dropna()
            y = y[X.index]

            logger.info(f"Features preparadas: {X.shape}, Target: {y.shape}")
            logger.info(f"Features: {list(X.columns)}")

            return X, y

        except Exception as e:
            logger.error(f"Error preparando features: {e}")
            raise

    def _calculate_haversine_distance(
        self, lat1: pd.Series, lon1: pd.Series, lat2: pd.Series, lon2: pd.Series
    ) -> pd.Series:
        """Calcula distancia haversine entre dos puntos"""
        R = 6371  # Radio de la Tierra en km

        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))

        return R * c

    async def train_model(
        self, model_name: str, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2
    ) -> Dict[str, Any]:
        """Entrena un modelo específico y retorna métricas"""
        try:
            models_config = self.get_available_models()

            if model_name not in models_config:
                raise ValueError(
                    f"Modelo {model_name} no disponible. Opciones: {list(models_config.keys())}"
                )

            config = models_config[model_name]
            estimator = config["model"]
            preprocessor = StandardScaler() if config["requires_scaling"] else "passthrough"
            model = Pipeline(
                steps=[("preprocessor", preprocessor), ("estimator", estimator)]
            )

            logger.info(f"Entrenando modelo: {model_name}")

            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            # Entrenar un artefacto único que incluye todo el preprocesamiento.
            start_time = datetime.now()
            model.fit(X_train, y_train)
            training_time = (datetime.now() - start_time).total_seconds()

            # Predicciones
            y_pred = model.predict(X_test)

            # Calcular métricas
            metrics = self._calculate_metrics(y_test, y_pred)
            metrics["training_time_seconds"] = training_time
            metrics["train_size"] = len(X_train)
            metrics["test_size"] = len(X_test)

            logger.info(
                f"Modelo {model_name} entrenado - RMSE: {metrics['rmse']:.2f}, R²: {metrics['r2_score']:.3f}"
            )

            return {
                "model": model,
                "model_name": model_name,
                "metrics": metrics,
                "hyperparams": config["params"],
                "features": list(X.columns),
            }

        except Exception as e:
            logger.error(f"Error entrenando modelo {model_name}: {e}")
            raise

    async def train_all_models(
        self, X: pd.DataFrame, y: pd.Series
    ) -> List[Dict[str, Any]]:
        """Entrena todos los modelos disponibles"""
        results = []
        models = self.get_available_models()

        logger.info(f"Iniciando entrenamiento de {len(models)} modelos...")

        for model_name in models.keys():
            try:
                result = await self.train_model(model_name, X, y)
                results.append(result)
                logger.info(f"✅ {model_name} completado")
            except Exception as e:
                logger.error(f"❌ Error en {model_name}: {e}")
                continue

        # Ordenar por RMSE (mejor primero)
        results.sort(key=lambda x: x["metrics"]["rmse"])

        logger.info(
            f"Entrenamiento completado. Mejor modelo: {results[0]['model_name'] if results else 'Ninguno'}"
        )

        return results

    def _calculate_metrics(
        self, y_true: pd.Series, y_pred: np.ndarray
    ) -> Dict[str, float]:
        """Calcula métricas de evaluación"""
        return {
            "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
            "mae": mean_absolute_error(y_true, y_pred),
            "r2_score": r2_score(y_true, y_pred),
        }

    async def predict_with_model(
        self, model: Any, features: TripFeatures, scaler: Any = None
    ) -> float:
        """Realiza predicción con un modelo específico"""
        try:
            # Convertir features a array
            feature_array = np.array(
                [
                    [
                        features.distance_km,
                        features.passenger_count,
                        features.vendor_id,
                        features.hour_of_day,
                        features.day_of_week,
                        features.month,
                        features.is_weekend,
                        features.is_rush_hour,
                    ]
                ]
            )

            # Compatibilidad con artefactos históricos. Los nuevos artefactos son
            # Pipelines autocontenidos y no requieren estado externo.
            if scaler is not None:
                feature_array = scaler.transform(feature_array)

            # Predicción
            prediction = model.predict(feature_array)[0]

            return float(prediction)

        except Exception as e:
            logger.error(f"Error en predicción: {e}")
            raise

    def get_feature_importance(
        self, model: Any, feature_names: List[str]
    ) -> Dict[str, float]:
        """Obtiene importancia de features si el modelo lo soporta"""
        try:
            estimator = (
                model.named_steps["estimator"]
                if isinstance(model, Pipeline)
                else model
            )
            if hasattr(estimator, "feature_importances_"):
                importance = estimator.feature_importances_
                return dict(zip(feature_names, importance))
            elif hasattr(estimator, "coef_"):
                # Para modelos lineales, usar valor absoluto de coeficientes
                importance = np.abs(estimator.coef_)
                return dict(zip(feature_names, importance))
            else:
                logger.warning(f"Modelo {type(model)} no soporta feature importance")
                return {}
        except Exception as e:
            logger.error(f"Error obteniendo feature importance: {e}")
            return {}
