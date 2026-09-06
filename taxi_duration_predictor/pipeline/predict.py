"""One request selects one artifact; its prediction carries that artifact's evidence."""

import math
from datetime import datetime, timezone

import pandas as pd

from ..adapters.ml.features import TripFeatureTransformer, canonical_raw
from ..adapters.ml.mlflow_adapter import MLflowAdapter, ModelUnavailable
from ..domain.entities import Prediction, TripFeatures


class PredictionPipeline:
    def __init__(self, mlflow_config=None):
        self.mlflow_adapter = MLflowAdapter(**(mlflow_config or {}))

    async def predict_trip_duration(
        self,
        pickup_lat,
        pickup_lon,
        dropoff_lat,
        dropoff_lon,
        passenger_count=1,
        vendor_id=1,
        pickup_datetime=None,
    ):
        raw = canonical_raw(
            pd.DataFrame(
                [
                    {
                        "pickup_latitude": pickup_lat,
                        "pickup_longitude": pickup_lon,
                        "dropoff_latitude": dropoff_lat,
                        "dropoff_longitude": dropoff_lon,
                        "passenger_count": passenger_count,
                        "vendor_id": vendor_id,
                        "pickup_datetime": pickup_datetime
                        if pickup_datetime is not None
                        else datetime.now(timezone.utc),
                    }
                ]
            )
        )
        # Validate the request independently before model failures are classified.
        TripFeatureTransformer().transform(raw)
        loaded = await self.mlflow_adapter.load_selected_model()
        try:
            engineered = loaded.model.named_steps["features"].transform(raw).iloc[0]
            duration = float(loaded.model.predict(raw)[0])
        except Exception as exc:
            raise ModelUnavailable("Selected artifact failed inference") from exc
        if not math.isfinite(duration) or not 0.5 <= duration <= 360:
            raise ModelUnavailable("Selected artifact returned an unsupported duration")
        features = TripFeatures(
            **engineered.to_dict(), pickup_datetime=raw["pickup_datetime"].iloc[0].to_pydatetime()
        )
        return Prediction(
            predicted_duration_minutes=duration,
            confidence_score=None,
            confidence_status="NOT_AVAILABLE",
            model_version=loaded.info["run_id"],
            features_used=features,
            created_at=datetime.now(timezone.utc),
            model_info=loaded.info,
        )

    async def predict(self, prediction_data):
        prediction = await self.predict_trip_duration(
            pickup_lat=prediction_data["pickup_latitude"],
            pickup_lon=prediction_data["pickup_longitude"],
            dropoff_lat=prediction_data["dropoff_latitude"],
            dropoff_lon=prediction_data["dropoff_longitude"],
            passenger_count=prediction_data.get("passenger_count", 1),
            vendor_id=prediction_data.get("vendor_id", 1),
            pickup_datetime=prediction_data.get("pickup_datetime"),
        )
        return {
            "predicted_duration_minutes": prediction.predicted_duration_minutes,
            "model_version": prediction.model_version,
            "model": prediction.model_info,
            "confidence_score": None,
            "confidence_status": "NOT_AVAILABLE",
        }

    async def get_model_status(self):
        try:
            loaded = await self.mlflow_adapter.load_selected_model()
            return {"status": "ready", "model_info": loaded.info}
        except ModelUnavailable as exc:
            return {"status": "unavailable", "message": str(exc)}
