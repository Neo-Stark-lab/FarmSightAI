# FarmSight AI Architecture

## Purpose and scope

FarmSight AI is an explainable digital farm twin for small and marginal farmers in Tamil Nadu. The first deeply implemented capability is **zone-level water-stress risk and irrigation intelligence** for rice, groundnut, and maize. It supports decisions to inspect a zone and consider irrigation based on local conditions; it does not infer exact irrigation quantity from satellite data alone.

This document is the system-boundary contract for all implementation laps. The normative object shapes are in [data-model.md](data-model.md), HTTP shapes are in [api-contract.md](api-contract.md), and the pipeline-to-ML exchange is in [ml-contract.md](ml-contract.md).

## System shape

```text
React + TypeScript client
        | HTTPS JSON (API contract only)
        v
FastAPI application / orchestration layer
  | persistence (PostgreSQL + PostGIS)      | analysis jobs
  v                                         v
Farm, Zone, Observation, ...          Data pipeline -> FeatureSet -> ML adapter
                                                |               |
                                            source adapters    Prediction
                                                \               /
                                          evidence + explanation + recommendation boundary
```

The API is the only boundary the frontend crosses. Source adapters, raster processing, feature engineering, models, agricultural rules, and explainability must not be invoked by the client directly.

## Components and ownership

| Component | Responsibility | Must not do |
| --- | --- | --- |
| `frontend/` | Farmer input flow, map/zones, status, evidence and uncertainty presentation | Calculate risk, invent a recommendation, call data providers |
| `backend/` | API validation, authorization when introduced, persistence, job orchestration, contract serialization | Embed crop rules or silently substitute data |
| `data/` | Provider adapters, raw provenance, spatial/temporal aggregation, feature production | Train models or express farmer advice |
| `ml/` | Validate `FeatureSet`, score a versioned model, emit `Prediction` | Fetch providers, choose zones, set recommendations |
| agricultural-rules module | Versioned, reviewable agronomic policy from prediction/evidence/context to candidate recommendation | Claim exact water volume or present a risk as fact |
| explainability module | Translate evidence, feature contributions and data quality into traceable explanations/confidence context | Alter score, manufacture evidence, promise correctness |

## Backend architecture

Use a versioned `/api/v1` FastAPI surface. Routers stay thin; services coordinate transactions and analysis jobs; repositories isolate PostgreSQL/PostGIS access; adapters isolate pipeline, ML, rules and explanation integrations. An analysis request creates an asynchronous `AnalysisRun`; it is not a long-running browser request. Idempotency is keyed by `Idempotency-Key` for farm creation and analysis submission.

Initial logical modules (not implementation requirements): `api`, `schemas`, `services`, `repositories`, `jobs`, `integrations`, and `config`. All timestamps use UTC RFC 3339 strings. IDs are UUIDs. Geometry is GeoJSON in EPSG:4326 at the API boundary and a validated PostGIS polygon internally.

## Frontend architecture

Use React + Vite + TypeScript. Keep API DTOs separate from view state. The farmer flow is: location and boundary -> crop and sowing date -> farm twin -> zones -> analysis status -> zone detail -> evidence/explanation -> conservative recommendation. The client must render missing, stale, partial, and failed-data states explicitly, including `data_freshness` and `confidence`; it must never create a risk score locally. Map geometry is submitted as GeoJSON and displayed from API responses.

## Data pipeline boundary

The pipeline accepts an immutable analysis context (`farm_id`, `zone_id`, geometry, crop, sowing date, analysis time) and produces source-attributed `Observation` records followed by an immutable `FeatureSet`. It records provider/source, observed time, retrieval/processing time, units, quality flags, spatial and temporal aggregation, and missingness. Raw source artefacts belong in `data/raw/` and derived artefacts in `data/processed/`; database records hold references and provenance, not mandatory duplicated rasters.

Satellite observations are observations made at their acquisition time and may arrive later; they are never labelled real-time. Data-source selection, licensing, coverage, and freshness thresholds are supplied by Claude 1 and integrated by Go 2, not guessed here.

## ML boundary

`ml/` accepts only the canonical versioned JSON `FeatureSet` in [ml-contract.md](ml-contract.md). It returns a versioned `Prediction` with a categorical water-stress risk, optional calibrated probability only when the deployed model justifies it, model/data confidence, and machine-readable contribution references. The backend validates feature schema/model compatibility before persistence. No model is trained or claimed accurate in this lap.

## Agricultural-rules and explainability boundaries

Agricultural rules are a separate, versioned policy input that receives prediction, evidence, crop context, and data-quality status. It produces a conditional `Recommendation`; it cannot overwrite predictions or infer exact irrigation quantity from satellite-only information. Claude 2 owns rule content.

Explainability joins stored evidence and ML contributions into user-facing reason statements. It identifies evidence gaps, staleness, and why confidence is limited. Confidence expresses model/data confidence, not certainty or a guaranteed outcome. Claude 3 owns wording and uncertainty policy.

## Persistence and lifecycle

PostgreSQL/PostGIS is the system of record. A Farm owns Zones; a Zone owns time-series Observations and FeatureSets. A FeatureSet is created for a zone and analysis run; it can yield one or more versioned Predictions. Evidence links to observations/features/predictions. Recommendations are derived, versioned artefacts linked to a prediction and evidence set. Records are append-only for observations, feature sets, predictions, evidence, and recommendations; corrections create superseding records rather than mutate history. See [data-model.md](data-model.md).

## Analysis sequence

1. Farmer creates a farm with boundary, crop and sowing date.
2. Backend validates boundary/crop/date and creates or updates the digital farm twin and zones.
3. Farmer submits analysis; backend creates `AnalysisRun` and returns `202`.
4. Pipeline obtains available source observations, records provenance/freshness, and generates one canonical FeatureSet per zone.
5. ML validates and scores each eligible FeatureSet, yielding Prediction records.
6. Rules and explainability derive conditional recommendations and traceable evidence without changing model output.
7. Backend marks the run complete, partial, or failed; frontend polls its status and retrieves zones/details.

## Errors, missingness, and staleness

Validation failures are `422`; unknown IDs are `404`; duplicate idempotent submission is replayed; an invalid state conflict is `409`; internal/provider/job failures use `5xx` or a failed analysis run. Every error follows the shared error envelope.

Missing values remain `null` with a required missingness/quality reason; they are never zero-filled without an explicit feature-engineering rule. A zone can be `insufficient_data`, and a run can be `partial`; neither is silently represented as low risk. Freshness is calculated from `observed_at` (or forecast generation time where relevant) to `analyzed_at`, using source-specific thresholds configured by the pipeline. The UI must show freshness and unavailable sources.

## Configuration conventions

Configuration comes from environment variables, with no secrets committed. Use uppercase names, a single `.env.example` later, and Pydantic/backend validation at startup. Required groups are: `APP_ENV`, `API_PREFIX`, `DATABASE_URL`, `CORS_ORIGINS`, `ANALYSIS_QUEUE_URL`, `ANALYSIS_RESULT_URL`, source credentials/endpoints such as `WEATHER_*` and `SATELLITE_*`, `ML_MODEL_URI`, `ML_MODEL_VERSION`, `ML_FEATURE_SCHEMA_VERSION`, and `LOG_LEVEL`. Feature freshness thresholds are named by source/metric (for example `FRESHNESS_NDVI_HOURS`) and must have documented defaults before implementation. Secrets are supplied only through deployment configuration.

## Non-negotiable scientific language

Use **water-stress risk**, **nutrient-stress risk**, and **soil-condition indicator**. Do not claim satellite measurement of exact NPK without ground validation, satellite real-time status, exact irrigation quantities from satellite alone, fabricated accuracy, or confidence as a guarantee.
