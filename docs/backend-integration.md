# Backend integration (Lap 6)

The FastAPI application at `backend/app/main.py` exposes the contract's `/api/v1` API. Routes validate and serialize only; `services.py` coordinates the pipeline, scoring adapter, explainability translator, recommendation engine and repository boundary.

## Endpoints

- `GET /health`
- `POST /api/v1/farms`, `GET /api/v1/farms/{farm_id}` and `GET /api/v1/farms/{farm_id}/zones`
- `POST /api/v1/farms/{farm_id}/analyze`, `GET /api/v1/analysis-runs/{analysis_run_id}`
- `GET /api/v1/zones/{zone_id}/evidence` and `/recommendation`

Farm and analysis submission accept `Idempotency-Key`; replaying a key returns the original resource. Geometry is stored and returned as supplied GeoJSON. The default repository is an in-memory test/development adapter behind a repository boundary. Production must replace it with PostgreSQL/PostGIS.

## Analysis flow

`Farm -> zone -> DataPipeline -> canonical FeatureSet -> WaterStressInference -> evidence_from_prediction -> recommendation_engine -> persisted result`.

The pipeline owns all feature construction and preserves source, timestamps, units, freshness and missing reasons. Missing values remain `null`; stale values retain their status. Prediction probability remains `null`; confidence is explicitly data/model-quality context rather than correctness probability. Contributions toward class 2/HIGH use `increases_risk`.

## Provider modes and limitations

`PROVIDER_MODE=fixture` is the default. It produces deterministic observations marked `DEMO DATA` and retains unavailable soil moisture as `null`. No external provider is contacted by a route. This checkout did not include the promised Lap 2–5 data, ML artifact, SHAP implementation, rules, frontend, or Python runtime. Consequently the supplied fixture scoring adapter is **not validated ML** and live provider/model mode is intentionally not implemented. Replace that adapter with the missing Lap 3 loader and repository with PostgreSQL/PostGIS before production.

## Local use

Create a Python 3.10+ environment, install `pip install -r backend/requirements.txt`, then run `uvicorn backend.app.main:app --reload`. Configure `CORS_ORIGINS`, `PROVIDER_MODE`, and `ML_MODEL_URI` via environment variables (see `backend/.env.example`).

Run backend tests with `PYTHONPATH=. pytest backend/tests -q`. The requested root `pytest tests -q` is not applicable: this checkout contains no root `tests/` directory. Frontend test/build cannot run because no frontend source or `package.json` exists in this checkout.
