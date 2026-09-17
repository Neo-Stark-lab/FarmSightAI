# Lap 4 — ChatGPT Go 2: Geospatial and Data Pipeline

## Mission
Build the pipeline that supplies the ML system.

## Input
Pull latest `main`, then read:
- `00_MASTER_CONTEXT.md`
- `docs/data-sources.md`
- `docs/ml-contract.md`
- `docs/agricultural-rules.md`

## Pipeline
Farm boundary
→ satellite retrieval/processing
→ weather
→ soil moisture where practical
→ temporal features
→ zones
→ ML feature vector

## Satellite
Where practical calculate:
- NDVI
- NDMI
- temporal changes

## Weather
Calculate:
- rainfall 7d
- rainfall 30d
- rainfall anomaly
- temperature
- temperature anomaly

## Soil Moisture
Use a verified source where practical.
Store:
- source
- timestamp
- spatial resolution
- freshness

## Zones
Generate meaningful zones from available spatial information. Do not create arbitrary zones without a documented basis.

## Baselines
Support:
- same-field historical comparison
- filtered nearby-field comparison where context permits

Nearby farms are not automatically comparable.

## Missing Data
Represent missing/stale observations explicitly.

## Demo Fallback
If live APIs are unreliable, provide clearly labelled sample/synthetic data. Never present synthetic data as real observations.

## Output
Create/update:
- data pipeline
- scripts
- `docs/data-pipeline.md`
- sample data if needed

## Acceptance
The ML module can receive correctly structured feature data from the pipeline.

## Commit
`git commit -m "lap 4: build geospatial data pipeline"`
