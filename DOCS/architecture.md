# Attributable model lifecycle

The active runtime is deliberately small: `TrainingPipeline` or the owned bootstrap generates raw trip rows, `SklearnModelsAdapter` fits a complete sklearn Pipeline, `MLflowAdapter` persists/selects it, and `PredictionPipeline` calls that loaded artifact from FastAPI. Domain entities represent request features and results; the older domain-service interfaces are separate teaching examples, not hidden runtime components.

## Artifact contract

The serialized Pipeline contains `TripFeatureTransformer`, its fitted StandardScaler (or passthrough for RandomForest), the estimator, and a copy of lifecycle metadata. The transformer validates raw NYC inputs, normalizes offset-aware timestamps to NYC, calculates Haversine distance and derives the eight ordered features. Training and serving use that same class. Its source fingerprint and feature version are part of provenance, because Python pickle references installed class code rather than embedding that code.

Training fits on a seed-42 random partition and calculates finite RMSE/MAE/R² on the holdout only. Provenance includes declared dataset identity, synthetic/operator kind, source and permission reference, ordered canonical dataset and holdout SHA-256 fingerprints, units, split configuration and feature fingerprint. The cohort ID hashes these fields. Conservative equality is required before comparing scores; different datasets, labels, orderings or splits cannot compete implicitly. Raw data is not persisted as an artifact. Hashes establish attribution, not permission or representativeness.

MLflow stores both the artifact and run metadata. Loading compares their complete evidence copies, then returns a `LoadedModel` containing the model and metadata from one selected run. The prediction response uses that object for both the number and its explanation. A separate later model-info request may legitimately see another run; it cannot rewrite the earlier response.

## Selection and failure semantics

Finished runs must have a model directory, supported provenance and finite measured validation metrics. Search is paginated. One configured cohort is ranked by RMSE, newest creation time, then run ID. Multiple cohorts without a selector are an error. An explicit run pin must be finished, attributable, in the configured experiment and compatible with an optional cohort pin. Training verifies its own newly saved winner rather than a global best from another batch; serving pins do not silently redirect this training verification.

Legacy metadata returns unavailable metrics and provenance safely; a legacy run cannot serve. Missing/broken artifacts, metadata disagreement, unknown cohort, failed inference or unsupported numeric output produce HTTP 503 without a guessed duration. Invalid raw input produces 422. `GET /health` is process liveness only. `GET /api/v1/health/` tests selection and artifact loading, not future request success.

## Tracking boundary

Every adapter reads the same environment configuration and uses its own `MlflowClient`; it does not depend on an active global MLflow run. Some supported MLflow versions internally consult a global tracking URI during artifact transfer even when a client is configured. The adapter serializes these synchronous artifact operations with a process-local lock and restores both the prior URI and the environment value, including on failure. Adapter configuration reads share that lock. Metadata calls remain client-bound. Applications embedding unrelated direct global-MLflow operations should isolate that runtime or use the same guard; this application has no such unguarded transfer path.

Compose uses MLflow's HTTP artifact proxy and a server-owned artifact directory. The API and trainer have no shared model volume. The Docker CI scenario proves this boundary with separate processes and an actual HTTP prediction tied to the training run.

## Evidence and limits

`tests/integration/test_model_lifecycle.py` exercises real raw-trip fit → artifact persistence → reload → HTTP inference and checks identity/provenance/numerical parity. Its adversarial scenarios cover cross-cohort scores, source/split changes, nonfinite metrics, search pages, tie order, legacy metadata, broken artifacts, selection changes and inference failures. No private data or paid provider is needed.

The tracker and model artifacts are trusted operator-controlled storage; pickle loading is not safe for untrusted models. The source/permission declaration is not automatically verified. Synthetic held-out errors measure the owned generator only. This reference does not establish real taxi accuracy, temporal generalization, calibrated confidence, cloud reliability or full PostgreSQL/dashboard correctness.
