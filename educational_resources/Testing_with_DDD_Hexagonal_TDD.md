# 🧪 Testing with Domain-Driven Design & Hexagonal Architecture

## 📚 Educational Guide for MLOps Testing Strategies

---

## 🎯 **Learning Objectives**

By the end of this guide, you will understand:
- How to structure tests following **Domain-Driven Design (DDD)** principles
- How to apply **Hexagonal Architecture** patterns to testing
- How to implement **Test-Driven Development (TDD)** in MLOps projects
- How to create **production-ready testing strategies** for machine learning systems

---

## 🏗️ **Part 1: Architecture-Driven Testing**

### **Why Architecture Matters for Testing**

In traditional testing, we often think "unit tests" and "integration tests." But with DDD and Hexagonal Architecture, we think in terms of **layers** and **boundaries**:

```
🔷 Domain Layer (Pure Business Logic)
   ↓
🔶 Application Layer (Use Cases)
   ↓
🔴 Adapters Layer (External Integrations)
   ↓
🟢 Infrastructure Layer (Databases, APIs, MLflow)
```

**Each layer has different testing needs and strategies.**

### **The Hexagonal Testing Strategy**

```
tests/
├── unit/                    # 🔷 Domain Layer Tests
│   ├── test_domain_entities.py     # Location, TripFeatures, Prediction
│   ├── test_domain_services.py     # Business logic & rules
│   └── test_value_objects.py       # TripDuration, validation rules
├── integration/             # 🔴 Adapter Layer Tests
│   ├── test_ml_adapters.py         # MLflow, model adapters
│   ├── test_data_adapters.py       # Database, file adapters
│   └── test_api_controllers.py     # FastAPI integration
├── e2e/                     # 🌐 Complete System Tests
│   ├── test_mlops_pipeline.py      # Training → Prediction flow
│   ├── test_api_endpoints.py       # Full API workflow
│   └── test_monitoring.py          # Dashboard & metrics
└── reports/                 # 📊 Test Documentation
    ├── coverage_html/       # Visual coverage reports
    ├── coverage.xml         # CI/CD integration
    └── junit.xml           # Test result reports
```

---

## 🔷 **Part 2: Domain-Driven Testing (Unit Tests)**

### **DDD Testing Principle: Test Business Logic First**

**Domain tests focus on**:
- ✅ **Entities**: Core business objects (TaxiTrip, Location)
- ✅ **Value Objects**: Immutable values (TripDuration, TripFeatures)
- ✅ **Domain Services**: Business rules and calculations
- ❌ **NO external dependencies**: No databases, APIs, or frameworks

### **Example: Testing Domain Entities**

```python
class TestLocation:
    """Test Location entity - Core business rules"""

    def test_location_validation_nyc_boundaries(self):
        """Test: Business rule - trips must be within NYC"""
        # ✅ Valid NYC location
        manhattan = Location(latitude=40.7831, longitude=-73.9712)
        assert manhattan.is_valid_nyc_location() is True

        # ❌ Invalid location (outside NYC)
        los_angeles = Location(latitude=34.0522, longitude=-118.2437)
        assert los_angeles.is_valid_nyc_location() is False

    def test_distance_calculation_haversine(self):
        """Test: Distance calculation using Haversine formula"""
        pickup = Location(latitude=40.7831, longitude=-73.9712)
        dropoff = Location(latitude=40.7590, longitude=-73.9845)

        distance = pickup.distance_to(dropoff)

        # Business expectation: Manhattan distances are typically 1-5km
        assert 1.0 <= distance <= 5.0
        assert isinstance(distance, float)
```

### **Example: Testing Value Objects**

```python
class TestTripDuration:
    """Test TripDuration value object - Validation rules"""

    def test_trip_duration_business_rules(self):
        """Test: Business rule - realistic trip durations"""
        # ✅ Valid duration (30 minutes)
        normal_trip = TripDuration(seconds=1800)
        assert normal_trip.is_valid() is True
        assert normal_trip.minutes == 30.0

        # ❌ Too short (10 seconds - likely data error)
        invalid_short = TripDuration(seconds=10)
        assert invalid_short.is_valid() is False

        # ❌ Too long (7 hours - likely data error)
        invalid_long = TripDuration(seconds=25200)
        assert invalid_long.is_valid() is False
```

### **DDD Testing Best Practices**

1. **Test Business Rules**: Each test should validate a specific business rule
2. **Use Domain Language**: Test names should match business terminology
3. **No Mocking**: Domain tests use real objects, no external dependencies
4. **Fast Execution**: Should run in milliseconds, suitable for TDD

---

## 🔶 **Part 3: Application Layer Testing**

### **Application Layer: Use Cases and Workflows**

Application layer tests focus on **orchestrating domain objects** to fulfill use cases:

```python
class TestTripPredictionService:
    """Test application service - Use case orchestration"""

    def test_predict_trip_duration_use_case(self):
        """Test: Complete prediction workflow"""
        # Arrange: Set up use case inputs
        trip_request = PredictionRequest(
            pickup_latitude=40.7831,
            pickup_longitude=-73.9712,
            dropoff_latitude=40.7590,
            dropoff_longitude=-73.9845,
            passenger_count=2,
            pickup_datetime="2023-01-15T14:30:00"
        )

        # Act: Execute use case
        service = TripPredictionService()
        prediction = service.predict_duration(trip_request)

        # Assert: Validate business outcomes
        assert prediction.predicted_duration_minutes > 0
        assert prediction.confidence_score >= 0.7
        assert prediction.features_used is not None
```

---

## 🔴 **Part 4: Integration Testing (Adapters)**

### **Integration Testing: External System Boundaries**

Integration tests verify that our **adapters** correctly interact with external systems:

```python
class TestMLflowAdapter:
    """Test MLflow integration - Model persistence"""

    @pytest.mark.asyncio
    async def test_model_save_and_load_cycle(self):
        """Test: Complete MLflow model lifecycle"""
        # Arrange: Create adapter with test configuration
        adapter = MLflowAdapter(
            tracking_uri="sqlite:///test_mlflow.db",
            experiment_name="test_experiment"
        )

        # Create mock model for testing
        mock_model = create_test_model()

        # Act: Save model
        run_id = await adapter.save_model(
            model=mock_model,
            model_name="TestModel",
            metrics={"rmse": 2.45, "mae": 1.87},
            features=["distance", "passenger_count"]
        )

        # Act: Load model
        loaded_model = await adapter.load_best_model()

        # Assert: Verify round-trip consistency
        assert run_id is not None
        assert loaded_model is not None

        # Test prediction consistency
        test_features = np.array([[2.5, 2, 1, 14, 6, 1, 1, 0]])
        original_prediction = mock_model.predict(test_features)
        loaded_prediction = loaded_model.predict(test_features)

        assert np.allclose(original_prediction, loaded_prediction)
```

### **Integration Testing Characteristics**

- ✅ **Real Dependencies**: Uses actual MLflow, databases, APIs
- ✅ **Configuration**: Test-specific configurations (test databases)
- ✅ **Cleanup**: Proper teardown of test resources
- ✅ **Error Handling**: Tests both success and failure scenarios

---

## 🌐 **Part 5: End-to-End Testing (System)**

### **E2E Testing: Complete MLOps Workflows**

End-to-end tests validate **entire business workflows** from start to finish:

```python
class TestMLOpsPipeline:
    """Test complete MLOps pipeline - Training to Prediction"""

    @pytest.mark.e2e
    async def test_complete_training_pipeline(self):
        """Test: Full model training and deployment workflow"""
        # 1. Data Preparation
        training_data = load_test_dataset()
        assert len(training_data) > 100  # Sufficient training data

        # 2. Feature Engineering
        features = engineer_features(training_data)
        assert features.shape[1] == 8  # Expected feature count

        # 3. Model Training
        trainer = ModelTrainer()
        model_info = await trainer.train_model(
            features=features,
            target=training_data['trip_duration'],
            model_type="RandomForest"
        )

        # 4. Model Validation
        assert model_info['rmse'] < 5.0  # Acceptable performance
        assert model_info['model_id'] is not None

        # 5. Model Deployment
        predictor = ModelPredictor()
        prediction = await predictor.predict({
            "pickup_latitude": 40.7831,
            "pickup_longitude": -73.9712,
            "dropoff_latitude": 40.7590,
            "dropoff_longitude": -73.9845,
            "passenger_count": 2
        })

        # 6. End-to-End Validation
        assert prediction['duration_minutes'] > 0
        assert prediction['confidence'] > 0.7
        assert prediction['model_version'] == model_info['model_id']
```

---

## 🚀 **Part 6: Test-Driven Development (TDD) in MLOps**

### **TDD Cycle: Red → Green → Refactor**

TDD in MLOps follows the same cycle but with domain-specific considerations:

#### **🔴 Red: Write Failing Test First**

```python
def test_trip_duration_prediction_accuracy(self):
    """Test: Model predictions should be within acceptable error range"""
    # This test will fail initially - we haven't built the model yet!
    predictor = TripDurationPredictor()

    test_trip = {
        "pickup_latitude": 40.7831,
        "pickup_longitude": -73.9712,
        "dropoff_latitude": 40.7590,
        "dropoff_longitude": -73.9845,
        "passenger_count": 2,
        "pickup_datetime": "2023-01-15T14:30:00"
    }

    prediction = predictor.predict(test_trip)

    # Business requirement: predictions within 20% of actual
    actual_duration = 15.5  # minutes (known from test data)
    error_percentage = abs(prediction - actual_duration) / actual_duration

    assert error_percentage <= 0.20  # ❌ This will fail initially
```

#### **🟢 Green: Make Test Pass (Minimum Code)**

```python
class TripDurationPredictor:
    """Minimum implementation to make test pass"""

    def predict(self, trip_data):
        # Simplest possible implementation
        # In real TDD, this might be a hard-coded value initially
        return 15.5  # ✅ Makes test pass
```

#### **🔵 Refactor: Improve Without Breaking Tests**

```python
class TripDurationPredictor:
    """Improved implementation - still passes tests"""

    def __init__(self):
        self.model = self._load_trained_model()

    def predict(self, trip_data):
        features = self._extract_features(trip_data)
        raw_prediction = self.model.predict([features])[0]
        return round(raw_prediction, 1)  # ✅ Still passes tests

    def _extract_features(self, trip_data):
        # Feature engineering logic
        pickup = Location(trip_data["pickup_latitude"], trip_data["pickup_longitude"])
        dropoff = Location(trip_data["dropoff_latitude"], trip_data["dropoff_longitude"])
        distance = pickup.distance_to(dropoff)

        return [
            distance,
            trip_data["passenger_count"],
            # ... other features
        ]
```

### **TDD Benefits in MLOps**

1. **Model Requirements**: Tests define what "good enough" means
2. **Regression Detection**: Catch performance degradation early
3. **Documentation**: Tests serve as specification for model behavior
4. **Refactoring Safety**: Improve models without breaking functionality

---

## 📊 **Part 7: MLOps-Specific Testing Patterns**

### **Model Performance Testing**

```python
class TestModelPerformance:
    """Test ML model performance requirements"""

    def test_model_accuracy_requirements(self):
        """Test: Model meets business accuracy requirements"""
        model = load_production_model()
        test_data = load_test_dataset()

        predictions = model.predict(test_data.features)
        rmse = calculate_rmse(predictions, test_data.targets)

        # Business requirement: RMSE < 3.0 minutes
        assert rmse < 3.0

    def test_model_prediction_latency(self):
        """Test: Model predictions are fast enough for real-time use"""
        model = load_production_model()
        test_features = create_sample_features()

        start_time = time.time()
        prediction = model.predict([test_features])
        end_time = time.time()

        latency_ms = (end_time - start_time) * 1000

        # Business requirement: predictions < 100ms
        assert latency_ms < 100
```

### **Data Quality Testing**

```python
class TestDataQuality:
    """Test data validation and quality checks"""

    def test_input_data_validation(self):
        """Test: Input data meets quality requirements"""
        validator = TripDataValidator()

        # Valid trip data
        valid_trip = {
            "pickup_latitude": 40.7831,
            "pickup_longitude": -73.9712,
            "dropoff_latitude": 40.7590,
            "dropoff_longitude": -73.9845,
            "passenger_count": 2
        }

        assert validator.is_valid(valid_trip) is True

        # Invalid trip data (outside NYC)
        invalid_trip = {
            "pickup_latitude": 34.0522,  # Los Angeles
            "pickup_longitude": -118.2437,
            "dropoff_latitude": 40.7590,
            "dropoff_longitude": -73.9845,
            "passenger_count": 2
        }

        assert validator.is_valid(invalid_trip) is False

    def test_feature_drift_detection(self):
        """Test: Detect when input features drift from training data"""
        drift_detector = FeatureDriftDetector()

        current_features = load_recent_features()
        training_features = load_training_features()

        drift_score = drift_detector.calculate_drift(
            current_features,
            training_features
        )

        # Business rule: drift score < 0.1 for stable model
        assert drift_score < 0.1
```

---

## 🔧 **Part 8: Test Environment Setup**

### **Test Configuration**

```python
# conftest.py - Shared test configuration
import pytest
import os
from pathlib import Path

# Test database configuration
TEST_DB_URI = "sqlite:///test_mlflow.db"
TEST_EXPERIMENT_NAME = "test_taxi_duration_prediction"

@pytest.fixture(scope="session")
def test_config():
    """Global test configuration"""
    return {
        "db_uri": TEST_DB_URI,
        "experiment_name": TEST_EXPERIMENT_NAME,
        "model_path": "test_models/",
        "data_path": "test_data/"
    }

@pytest.fixture(scope="function")
def clean_test_environment():
    """Clean test environment before each test"""
    # Setup
    test_db = Path("test_mlflow.db")
    if test_db.exists():
        test_db.unlink()

    yield

    # Cleanup
    if test_db.exists():
        test_db.unlink()
```

### **Test Execution Commands**

```bash
# Domain layer tests (fast, no dependencies)
source activate ds_env && pytest tests/unit/ -v

# Integration tests (with MLflow, databases)
source activate ds_env && pytest tests/integration/ -v

# End-to-end tests (complete workflows)
source activate ds_env && pytest tests/e2e/ -v

# All tests with coverage
source activate ds_env && pytest tests/ --cov=taxi_duration_predictor --cov-report=html

# TDD workflow (fast feedback)
source activate ds_env && pytest tests/unit/ --tb=short -x
```

---

## 📋 **Part 9: Test Documentation Strategy**

### **Test Reports and Visibility**

All test outputs go in **`tests/reports/`** for easy access:

```
tests/reports/
├── coverage_html/
│   └── index.html          # 📊 Visual coverage report
├── coverage.xml            # 🤖 CI/CD integration
├── junit.xml               # 📈 Test dashboards
└── pytest_report.html     # 📋 Detailed test results
```

### **Accessing Test Reports**

```bash
# Generate all reports
source activate ds_env && pytest tests/ \
    --cov=taxi_duration_predictor \
    --cov-report=html:tests/reports/coverage_html \
    --cov-report=xml:tests/reports/coverage.xml \
    --junit-xml=tests/reports/junit.xml \
    --html=tests/reports/pytest_report.html

# Open coverage report in browser
source activate ds_env && python -m webbrowser tests/reports/coverage_html/index.html
```

---

## 🎯 **Part 10: Testing Best Practices Summary**

### **Domain-Driven Testing Principles**

1. **Test Business Rules First**: Domain tests validate core business logic
2. **Use Ubiquitous Language**: Test names match business terminology
3. **Layer-Appropriate Testing**: Different strategies for different layers
4. **Fast Feedback**: Unit tests provide rapid TDD cycles

### **Hexagonal Architecture Testing**

1. **Test Boundaries**: Focus on adapter interfaces and contracts
2. **Mock External Systems**: Use test doubles for infrastructure
3. **Integration Points**: Verify external system interactions
4. **End-to-End Validation**: Complete workflow testing

### **MLOps Testing Specific**

1. **Model Performance**: Test accuracy, latency, and business metrics
2. **Data Quality**: Validate inputs and detect drift
3. **Pipeline Testing**: Complete training and prediction workflows
4. **Monitoring**: Test dashboard and alerting functionality

### **Test-Driven Development**

1. **Red-Green-Refactor**: Classic TDD cycle for reliable development
2. **Specification by Example**: Tests define expected behavior
3. **Regression Safety**: Catch breaking changes early
4. **Design Improvement**: TDD leads to better architecture

---

## 🚀 **Getting Started Checklist**

### **✅ Setting Up Your Testing Environment**

1. **Create test structure**:
   ```bash
   mkdir -p tests/{unit,integration,e2e,reports}
   touch tests/conftest.py
   ```

2. **Install testing dependencies**:
   ```bash
   source activate ds_env && pip install pytest pytest-cov pytest-html pytest-asyncio
   ```

3. **Configure pytest** (create `pytest.ini`):
   ```ini
   [tool:pytest]
   testpaths = tests
   markers =
       unit: Unit tests for domain logic
       integration: Integration tests with external systems
       e2e: End-to-end pipeline tests
   ```

4. **Write your first test**:
   ```python
   # tests/unit/test_first_domain_rule.py
   def test_basic_business_rule():
       """Test: Write your first business rule test here"""
       assert True  # Replace with actual business logic test
   ```

5. **Run tests**:
   ```bash
   source activate ds_env && pytest tests/unit/ -v
   ```

### **✅ Implementing TDD Workflow**

1. **Write failing test** (Red)
2. **Make test pass** (Green)
3. **Refactor code** (Blue)
4. **Repeat** for each new feature

---

## 📚 **Further Reading**

- **Domain-Driven Design**: Eric Evans - "Domain-Driven Design: Tackling Complexity in the Heart of Software"
- **Hexagonal Architecture**: Alistair Cockburn - "Ports and Adapters" pattern
- **Test-Driven Development**: Kent Beck - "Test Driven Development: By Example"
- **Testing Patterns**: Gerard Meszaros - "xUnit Test Patterns"

---

## 💡 **Key Takeaways**

1. **Architecture drives testing strategy** - different layers need different approaches
2. **Domain tests are the foundation** - fast, reliable, business-focused
3. **Integration tests verify boundaries** - ensure external systems work correctly
4. **E2E tests validate workflows** - complete business scenarios
5. **TDD improves design** - tests first leads to better architecture
6. **MLOps adds complexity** - model performance and data quality matter
7. **Documentation matters** - tests serve as living specification

**Remember**: Great testing makes great software. In MLOps, it also makes great models! 🎯✨

---

*This guide is part of the Session 13 MLOps educational resources. For more information, see the complete project structure and additional learning materials.*
