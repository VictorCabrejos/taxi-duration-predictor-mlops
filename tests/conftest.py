"""Shared deterministic fixtures for the local unit-test suite."""

from datetime import datetime, timedelta

import pytest

from taxi_duration_predictor.domain.entities import Location, TaxiTrip, TripDuration


@pytest.fixture
def sample_trip() -> TaxiTrip:
    pickup = datetime(2025, 1, 15, 8, 30)
    return TaxiTrip(
        id="synthetic-trip-001",
        vendor_id=1,
        pickup_datetime=pickup,
        dropoff_datetime=pickup + timedelta(minutes=15),
        passenger_count=2,
        pickup_location=Location(latitude=40.7580, longitude=-73.9855),
        dropoff_location=Location(latitude=40.7829, longitude=-73.9654),
        store_and_fwd_flag="N",
        trip_duration=TripDuration(seconds=900),
    )
