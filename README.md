# Taxi Duration Predictor MLOps

An educational reference implementation that shows how a taxi-duration model can move from domain logic to a testable API, experiment tracking, a dashboard, and containerized services.

## Why it exists

The repository demonstrates the engineering boundaries around a machine-learning model: domain entities and ports, model and database adapters, a training/prediction pipeline, FastAPI serving, MLflow tracking, and Streamlit observability. It is a portfolio and teaching system, not a hosted production service.

## Architecture

```mermaid
flowchart LR
    Client --> API[FastAPI controller]
    API --> Domain[Domain services and ports]
    Domain --> Model[scikit-learn / MLflow adapter]
    Domain --> Data[PostgreSQL adapter]
    Training[Training pipeline] --> Model
    Dashboard[Streamlit dashboard] --> API
    Dashboard --> Tracking[MLflow tracking server]
```

See [docs/architecture.md](docs/architecture.md) for responsibilities, runtime boundaries, and verified limitations.

## Quick start

Python 3.10 or newer is required.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[api,mlops,dev]"
python -m pytest
uvicorn taxi_duration_predictor.api.main:app --reload
```

The API documentation is then available at `http://localhost:8000/docs`; the dependency-light health endpoint is `GET /health`. Prediction endpoints require a usable model/tracking setup.

## Docker Compose

Docker is useful when the API, dashboard, PostgreSQL, and MLflow services need to be demonstrated together.

```bash
cd deployment
cp .env.docker.example .env.docker
# Replace every CHANGE_ME_LOCAL_ONLY value.
docker compose --env-file .env.docker config
docker compose --env-file .env.docker up --build
```

No functional credential is committed. Compose refuses to start without `POSTGRES_PASSWORD`. The local `.env.docker` file is ignored.

## Testing and quality

```bash
python -m pytest
python -m ruff check --select F taxi_duration_predictor tests/unit tests/conftest.py
python -m compileall -q taxi_duration_predictor
```

Unit tests cover deterministic domain rules and secrets-safe configuration. The scripts named `system_validation*.py` are optional live-service probes; they are not counted as unit tests and require running services.

## Data, model, and API requirements

- No NYC trip dataset, fitted production model, or MLflow run is bundled in the tracked tree.
- The bootstrap training path in `taxi_duration_predictor/pipeline/train.py` uses synthetic data and labels its MLflow runs accordingly.
- PostgreSQL access requires `DATABASE_URL`; there is no embedded database password.
- Model and data provenance must be recorded by the operator for any non-synthetic run.
- The sample coordinates in tests are synthetic examples and contain no person-level records.

## Repository map

- `taxi_duration_predictor/domain/`: entities, ports, and orchestration logic.
- `taxi_duration_predictor/adapters/`: PostgreSQL, scikit-learn, and MLflow integrations.
- `taxi_duration_predictor/pipeline/`: training and prediction workflows.
- `taxi_duration_predictor/api/`: FastAPI routes and application factory.
- `observability/dashboards/`: Streamlit dashboard.
- `deployment/`: Dockerfiles, Compose definitions, and placeholder-only configuration.
- `educational_resources/`: notebooks and supporting teaching material; review notebook outputs before reuse.

## Limitations

- This is a reference implementation, not an SLA-backed deployment.
- The default bootstrap is synthetic and cannot substantiate real-world accuracy claims.
- External integration tests for PostgreSQL, MLflow, the dashboard, and the full Compose stack are not part of the fast unit-test gate.
- CORS and deployment hardening must be configured for the intended environment.
- Dependency ranges support repeatable resolution but are not a byte-for-byte lock file.

## Educational value

The project supports a guided comparison between pure domain rules and infrastructure adapters, then extends that lesson to experiment tracking, model serving, observability, and container orchestration. It is suitable as a production-ML case study or a workshop spine when the instructor supplies an approved dataset and clearly distinguishes synthetic metrics from measured results.

## License

Licensed under the [MIT License](LICENSE).
