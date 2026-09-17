# FarmSight AI ML Contract

## Boundary

Go 2/the pipeline produces a validated JSON FeatureSet; Gemini 1/the ML component consumes it and returns a JSON Prediction payload. The ML component must not fetch data, query the database, or make recommendation decisions. Contract version `1.0` is used unless both sides deliberately release a compatible new version.

## Request: `WaterStressScoringRequest`

```json
{
  "schema_version": "1.0",
  "request_id": "uuid",
  "analysis_run_id": "uuid",
  "feature_set_id": "uuid",
  "farm_id": "uuid",
  "zone_id": "uuid",
  "reference_time": "2026-09-17T00:00:00Z",
  "features": {
    "ndvi_current": 0.62,
    "ndvi_7d_change": -0.03,
    "ndvi_30d_change": -0.08,
    "ndmi_current": 0.14,
    "ndmi_change": -0.05,
    "rainfall_7d": 12.4,
    "rainfall_30d": 54.1,
    "rainfall_anomaly": -18.2,
    "temperature_mean": 31.1,
    "temperature_anomaly": 1.4,
    "soil_moisture": null,
    "soil_moisture_change": null,
    "crop": "rice",
    "crop_stage": "vegetative",
    "historical_deviation": -0.11,
    "neighboring_deviation": -0.07
  },
  "feature_metadata": { "ndvi_current": { "unit": "unitless", "source_observation_ids": ["uuid"], "freshness": { "age_hours": 36, "status": "fresh", "threshold_hours": 120 }, "missing_reason": null } },
  "quality_status": "partial"
}
```

All listed feature keys are required; their numeric values may be `null` only where `feature_metadata[key].missing_reason` is non-null. Categorical `crop` is `rice|groundnut|maize`; `crop_stage` is `initial|vegetative|reproductive|maturity|unknown`. `unknown` requires a quality flag. Numeric units: NDVI/NDMI and deviations are `unitless`; rainfall/anomaly is `mm` over documented reference climatology; `temperature_mean`/anomaly is `degC`; soil moisture is `m3_m3`; changes use the same unit as their base value. `historical_deviation` and `neighboring_deviation` must document baseline/comparison in metadata. Neighbor data must be privacy-filtered and aggregated before this boundary.

`feature_metadata` is required for every key and contains: `unit`, `source_observation_ids` (UUID array, possibly empty only for derived crop context), `freshness` (`age_hours`, `status`, `threshold_hours?`), `missing_reason` (`null|not_available|cloud_obscured|out_of_coverage|provider_error|invalid`), and optional `calculation`/`window`. The request fails validation if schema version, IDs, enum, unit, or metadata alignment is wrong.

## Eligibility and null policy

The pipeline sets `quality_status`: `complete` (all model-required inputs present/fresh), `partial` (optional inputs absent or stale but model can score), or `insufficient_data` (model-required input unavailable/stale). The model publishes its required/optional feature manifest with its version. It may score a partial set only when its manifest explicitly supports the missingness pattern. It must return `unknown` rather than impute an undocumented value. A model may use explicit, versioned imputation internally only if the output reports it in `input_quality_flags`.

## Response: `WaterStressScoringResponse`

```json
{
  "schema_version": "1.0",
  "request_id": "uuid",
  "prediction": {
    "prediction_type": "water_stress_risk",
    "risk_level": "moderate",
    "probability": null,
    "confidence": { "level": "medium", "score": null, "basis": ["recent vegetation-moisture decline", "soil-moisture input unavailable"] },
    "model_name": "water-stress-model",
    "model_version": "pending-release",
    "feature_schema_version": "1.0",
    "predicted_at": "2026-09-17T00:01:00Z",
    "status": "valid",
    "input_quality_flags": ["soil_moisture:not_available"],
    "contributions": [
      { "feature": "ndmi_change", "direction": "increases_risk", "magnitude": 0.31, "method": "model_native_or_shap", "source_observation_ids": ["uuid"] }
    ]
  }
}
```

`risk_level` is `low|moderate|high|unknown`; only `low|moderate|high` may have `status: valid`. `probability` is nullable and may be present only for a calibrated, documented model; it must never be labelled confidence. `confidence.level` is `low|medium|high`, represents model/data confidence, and is never a correctness guarantee. `score` is nullable unless the model has documented calibration/meaning. Contributions are optional, directional, feature-attributable, and must cite source observations where possible; they are evidence for explanation, not causal proof.

For an ineligible request, return HTTP/domain result `status: insufficient_data`, `risk_level: unknown`, `probability: null`, low confidence, and quality flags. For a technical scoring failure, return `status: failed` with a machine-readable error; do not substitute a fabricated prediction.

## Compatibility, validation, and observability

The pipeline validates its generated FeatureSet against this contract before queuing; ML validates again before scoring; backend validates the response before persistence. All logs/metrics include `request_id`, `analysis_run_id`, `zone_id`, model version, and schema version, without leaking farmer-identifying data. Breaking field, unit, enum, or semantic changes require a new major schema version and a coordinated backend release.
