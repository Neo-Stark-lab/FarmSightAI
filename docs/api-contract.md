# FarmSight AI API Contract

## Conventions

Base path: `/api/v1`. JSON keys are `snake_case`; IDs are UUID strings; timestamps are UTC RFC 3339. Geometry is GeoJSON EPSG:4326. All responses include `request_id`. Authentication is intentionally undecided for this prototype and must be introduced consistently before multi-user deployment.

Error envelope:

```json
{ "request_id": "uuid", "error": { "code": "validation_error", "message": "Human-readable summary", "details": [{ "field": "boundary", "reason": "must be a valid polygon" }] } }
```

Use `400` malformed JSON, `404` absent resource, `409` state conflict, `422` semantic validation, `429` rate limit, and `5xx` unavailable dependency/internal error. A completed analysis with missing source data is not an HTTP error: it is `partial` or `insufficient_data` in its resource/status.

## Farm creation

`POST /farms` accepts `Idempotency-Key` and:

```json
{ "name": "North field", "location": { "type": "Point", "coordinates": [80.27, 13.08] }, "boundary": { "type": "Polygon", "coordinates": [] }, "crop": "rice", "sowing_date": "2026-08-01", "timezone": "Asia/Kolkata" }
```

Respond `201` with `{request_id, farm}` using the Farm shape. Reject future sowing dates, unsupported crops, invalid geometry, or a boundary/location inconsistency. Zone generation is not implied by this request unless its response explicitly reports it.

## Farm and zone retrieval

`GET /farms/{farm_id}` returns `200 {request_id, farm, latest_analysis?: {id,status,analysis_reference_time}}`.

`GET /farms/{farm_id}/zones?analysis_run_id={uuid?}` returns `200 {request_id, farm_id, analysis_run_id?, zones:[{zone, latest_prediction?, data_freshness?, recommendation_status?}]}`. Omission selects the latest completed/partial run; a zone without a result states `prediction.status: insufficient_data|failed`, never an inferred low risk.

`GET /zones/{zone_id}` returns `200 {request_id, zone, farm, latest_prediction?, data_freshness?, latest_recommendation?}`. It must include `analysis_run_id` beside any analytical result.

## Analysis

`POST /farms/{farm_id}/analyze` accepts `Idempotency-Key` and optional `{ "reference_time": "timestamp", "force_refresh": false }`. It validates farm status and returns `202 {request_id, analysis_run:{id,status:"queued",farm_id,requested_at,analysis_reference_time}}`. It does not return fabricated immediate analysis.

`GET /analysis-runs/{analysis_run_id}` returns `{request_id, analysis_run}`. `completed` means all eligible zones completed; `partial` means one or more zones/source stages did not complete; `failed` has `failure_code` and safe message. Clients poll this endpoint, then request zones.

## Zone explanation and recommendation

`GET /zones/{zone_id}/evidence?analysis_run_id={uuid?}` returns `200 {request_id, zone_id, analysis_run_id, prediction?, evidence:[], data_freshness:{overall_status, items:[]}, limitations:[]}`. Evidence preserves source, observation time, quality flags and trace links.

`GET /zones/{zone_id}/recommendation?analysis_run_id={uuid?}` returns `200 {request_id, zone_id, analysis_run_id, recommendation}`. `recommendation` uses the normative data model. If unavailable, return `{status:"not_available", limitations:[...], action:null}` with `200`, not invented guidance.

## Contract behavior required of clients

Clients display `risk_level` as water-stress **risk**, not fact; present `confidence` as model/data confidence; display freshness/limitations with the result; show conditional recommendation text verbatim; and distinguish `unknown`, `insufficient_data`, `partial`, and `failed`. `probability` is omitted/null unless the response documents a calibrated model output. The API never claims real-time satellite data, exact NPK, or exact satellite-only irrigation quantity.
