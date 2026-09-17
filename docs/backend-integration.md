# LAP 6 backend integration

FastAPI exposes the versioned contract and keeps routes thin. `FarmService` validates and persists farm/zone records; `AnalysisService` constructs `AnalysisContext`, calls the existing `DataPipeline`, then `score_water_stress` (which invokes the existing SHAP explainer), and finally `RecommendationEngine.evaluate`.

The repository is an in-memory local/test adapter behind a persistence boundary; PostgreSQL/PostGIS remains the production system of record. Farm and analysis submissions replay the same resource for the same `Idempotency-Key`. CORS origins and API prefix are environment-configurable.

Missing values, crop stage `unknown`, source metadata and freshness are retained from pipeline output. Fixture providers must be explicitly supplied by deployment/test wiring and their observations remain demo data. Probability and confidence are returned separately by the ML module.

Run `pip install -r requirements.txt -r backend/requirements.txt`, `pytest tests -q`, `PYTHONPATH=. pytest backend/tests -q`, then `cd frontend && npm install && npm run test && npm run build`.
