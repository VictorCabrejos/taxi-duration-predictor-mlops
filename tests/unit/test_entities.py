from datetime import datetime

import pytest

from taxi_duration_predictor.domain.entities import Location, TripDuration, TripFeatures


def test_location_distance_is_symmetric() -> None:
    a = Location(latitude=40.7580, longitude=-73.9855)
    b = Location(latitude=40.7829, longitude=-73.9654)

    assert a.distance_to(b) == pytest.approx(b.distance_to(a))
    assert 3.0 < a.distance_to(b) < 4.0


@pytest.mark.parametrize("seconds", [30, 900, 21600])
def test_trip_duration_accepts_documented_bounds(seconds: float) -> None:
    assert TripDuration(seconds=seconds).is_valid()


@pytest.mark.parametrize("seconds", [29.9, 21600.1])
def test_trip_duration_rejects_values_outside_bounds(seconds: float) -> None:
    assert not TripDuration(seconds=seconds).is_valid()


def test_trip_features_are_derived_from_domain_entity(sample_trip) -> None:
    features = TripFeatures.from_trip(sample_trip)

    assert features.passenger_count == 2
    assert features.hour_of_day == 8
    assert features.is_rush_hour == 1
    assert features.pickup_datetime == datetime(2025, 1, 15, 8, 30)
    assert features.to_array().shape == (8,)


def test_trip_validation_rejects_non_nyc_location(sample_trip) -> None:
    sample_trip.dropoff_location = Location(latitude=34.0522, longitude=-118.2437)
    assert not sample_trip.is_valid()
