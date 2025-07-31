"""
Test Configuration for Taxi Duration Predictor
Configuración central para todos los tests del proyecto
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test database configuration
TEST_DB_URI = "sqlite:///data/test_mlflow.db"
TEST_EXPERIMENT_NAME = "test_taxi_duration_prediction"

# Test data paths
TEST_DATA_DIR = project_root / "tests" / "fixtures"
TEST_REPORTS_DIR = project_root / "tests" / "reports"

# Ensure test directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_REPORTS_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def test_config():
    """Global test configuration"""
    return {
        "db_uri": TEST_DB_URI,
        "experiment_name": TEST_EXPERIMENT_NAME,
        "data_dir": TEST_DATA_DIR,
        "reports_dir": TEST_REPORTS_DIR,
    }


@pytest.fixture(scope="function")
def sample_trip_data():
    """Sample trip data for testing"""
    return {
        "pickup_latitude": 40.7831,
        "pickup_longitude": -73.9712,
        "dropoff_latitude": 40.7590,
        "dropoff_longitude": -73.9845,
        "passenger_count": 2,
        "vendor_id": 1,
        "pickup_datetime": "2023-01-15 14:30:00",
    }


# Cleanup after tests
def pytest_sessionfinish(session, exitstatus):
    """Clean up test artifacts after session"""
    test_db_file = Path("data/test_mlflow.db")
    if test_db_file.exists():
        try:
            test_db_file.unlink()
        except PermissionError:
            pass  # File might be in use
