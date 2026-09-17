# FarmSight AI Data Model Contract

## Conventions

All IDs are UUID strings; all timestamps are UTC RFC 3339 `date-time`; all numeric measures are JSON numbers with an explicit `unit`; all enums are lower snake case. `required` means required on creation of that object. `nullable` means it may be `null` when unavailable. `source` identifies an origin/provider and is not a claim of measurement accuracy. `freshness` is calculated at analysis time from source observation time, not retrieval time.

Common audit fields on every persisted entity: `id` (required UUID), `created_at` (required), `updated_at` (required). Immutable analytical entities also have `supersedes_id` (optional UUID) to correct without destroying history.

## Farm

| Field | Type | Status | Notes |
| --- | --- | --- | --- |
| `id` | UUID | required | Primary key |
| `name` | string, 1–120 | required | Farmer-visible label |
| `location` | GeoJSON Point | required | EPSG:4326 representative point |
| `boundary` | GeoJSON Polygon/MultiPolygon | required | EPSG:4326; valid, non-self-intersecting |
| `area_hectares` | number | server-derived | Geodesic calculated value |
| `crop` | enum `rice|groundnut|maize` | required | Current planted crop |
| `sowing_date` | date | required | Cannot be future date |
| `timezone` | IANA string | required | Default `Asia/Kolkata` for target scope |
| `status` | enum `active|archived` | required | Lifecycle |

Relationships: Farm has many Zones and AnalysisRuns. Crop/sowing date are snapshot into FeatureSet for reproducibility.

## Zone

| Field | Type | Status | Notes |
| --- | --- | --- | --- |
| `id`, `farm_id` | UUID | required | Farm foreign key |
| `name` | string | required | Stable farmer-visible label |
| `geometry` | GeoJSON Polygon/MultiPolygon | required | Must be within farm boundary |
| `area_hectares` | number | server-derived | |
| `zone_method` | enum `manual|grid|segmentation|other` | required | Creation provenance |
| `zone_method_version` | string | optional | Required if algorithmic |
| `status` | enum `active|retired` | required | |

Zone has many Observations, FeatureSets, Predictions, Evidence and Recommendations. Zones do not themselves contain a mutable “current risk”; the API selects latest eligible analytical records.

## Observation

An atomic or aggregated source measurement/reference for a zone.

| Field | Type | Status | Notes |
| --- | --- | --- | --- |
| `id`, `farm_id`, `zone_id` | UUID | required | Provenance scope |
| `metric` | string enum/catalog key | required | e.g. `ndvi`, `rainfall`, `soil_moisture` |
| `value` | number | nullable | Null only with quality/missing reason |
| `unit` | string | required | NDVI/NDMI use `unitless`; rainfall `mm` |
| `observed_at` | timestamp | required | Measurement/event time |
| `period_start`, `period_end` | timestamp | optional | Required for accumulated/aggregated values |
| `source` | object | required | `{provider, dataset, product, source_record_id?}` |
| `retrieved_at`, `processed_at` | timestamp | required | Acquisition and processing time |
| `spatial_aggregation` | string | required | e.g. `zone_mean`, `zone_median` |
| `quality_flags` | string[] | required | Empty array permitted |
| `missing_reason` | enum | nullable | `not_available|cloud_obscured|out_of_coverage|provider_error|invalid` |
| `freshness` | object | required | `{age_hours, status: fresh|stale|unknown, threshold_hours?}` at analysis time |

Observation is immutable and may be referenced by many FeatureSets/Evidence records.

## FeatureSet

An immutable, one-zone ML-ready feature vector for an AnalysisRun. Exact shape is normative in [ml-contract.md](ml-contract.md).

| Field | Type | Status | Notes |
| --- | --- | --- | --- |
| `id`, `analysis_run_id`, `farm_id`, `zone_id` | UUID | required | Scope and relationships |
| `schema_version` | string | required | ML contract version |
| `feature_values` | object | required | Exact feature keys; nulls allowed only with metadata |
| `feature_metadata` | object | required | Per-feature unit/source/observation refs/freshness/missingness |
| `reference_time` | timestamp | required | End time of analysis window |
| `crop`, `crop_stage` | enum | required | Snapshot; crop stage may be `unknown` only with flag |
| `quality_status` | enum `complete|partial|insufficient_data` | required | Eligibility signal |
| `generated_at` | timestamp | required | |

## Prediction

| Field | Type | Status | Notes |
| --- | --- | --- | --- |
| `id`, `feature_set_id`, `analysis_run_id`, `farm_id`, `zone_id` | UUID | required | Traceability |
| `prediction_type` | literal `water_stress_risk` | required | Initial core feature |
| `risk_level` | enum `low|moderate|high|unknown` | required | `unknown` for ineligible inference |
| `probability` | number 0–1 | nullable | Only if model documentation supports calibrated probability |
| `confidence` | object | required | `{level: low|medium|high, score?: 0..1, basis: string[]}`; never guarantee |
| `model_name`, `model_version`, `feature_schema_version` | string | required | Compatibility/reproducibility |
| `predicted_at` | timestamp | required | |
| `status` | enum `valid|insufficient_data|failed|superseded` | required | |
| `contribution_refs` | UUID[] | required | Evidence/contribution references; may be empty |

## Evidence

Evidence is a traceable fact or model contribution; it is not an unsupported causal claim.

| Field | Type | Status | Notes |
| --- | --- | --- | --- |
| `id`, `farm_id`, `zone_id`, `analysis_run_id` | UUID | required | Scope |
| `prediction_id` | UUID | optional | Required for model-specific evidence |
| `kind` | enum `observation|feature|model_contribution|data_quality|context` | required | |
| `label` | string | required | Stable human-readable heading |
| `value` | number/string/object | required | Structured value |
| `unit` | string | optional | |
| `direction` | enum `increases_risk|decreases_risk|neutral|unknown` | optional | Applicable to contributions only |
| `source_observation_ids`, `feature_set_id` | UUID[]/UUID | optional | At least one provenance link required |
| `observed_at`, `freshness` | timestamp/object | optional | Required for observation-derived evidence |
| `created_at` | timestamp | required | |

## Recommendation

| Field | Type | Status | Notes |
| --- | --- | --- | --- |
| `id`, `farm_id`, `zone_id`, `analysis_run_id`, `prediction_id` | UUID | required | Prediction must be valid or explicitly low-confidence |
| `status` | enum `active|superseded|not_available` | required | |
| `priority` | enum `low|medium|high` | required | Attention priority, not risk probability |
| `action` | string | required | Conditional, conservative farmer action |
| `conditions` | string[] | required | e.g. verify field conditions/reassess if rain expected |
| `rationale_evidence_ids` | UUID[] | required | Traceability |
| `rule_set_version` | string | required | Agricultural policy provenance |
| `issued_at`, `valid_until` | timestamp | required | Expiry makes staleness explicit |
| `limitations` | string[] | required | Includes unavailable/stale evidence as applicable |

Recommendations never contain satellite-derived exact irrigation volume. A `not_available` recommendation is valid when evidence is inadequate.

## AnalysisRun

Internal orchestration record exposed as status response: `id` UUID, `farm_id` UUID, `requested_at` timestamp, `started_at?`, `completed_at?`, `requested_by?`, `status` (`queued|running|completed|partial|failed`), `zone_count`, `completed_zone_count`, `failure_code?`, `failure_message?`, and `analysis_reference_time` timestamp. It owns FeatureSets and joins downstream records.
