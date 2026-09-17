# Lap 1 — Claude 1: Data Source Verification

## Mission
Verify practical free/open data sources for FarmSight.

## Input
Pull latest `main`, then read:
- `00_MASTER_CONTEXT.md`
- `docs/architecture.md`
- `docs/ml-contract.md`

## Research
Verify official documentation for:
- Sentinel-2
- ISRO/Bhoonidhi
- NISAR soil moisture
- Open-Meteo
- NASA POWER
- Tamil Nadu agricultural datasets
- Other useful public sources only if genuinely relevant

## Record For Each Source
- Official source
- Access method
- Variables
- Spatial resolution
- Temporal resolution
- Historical availability
- Update frequency
- API/download method
- Restrictions
- Licensing
- Practicality for the hackathon
- Limitations

## Specifically Determine
Which sources can practically provide:
- NDVI
- NDMI
- rainfall
- temperature
- soil moisture
- historical agricultural context

## Output
Create:
`docs/data-sources.md`

Keep code limited to useful access examples.

## Guardrails
Do not claim:
- exact NPK from satellite
- real-time satellite measurements
- unsupported field-level accuracy

## Acceptance
A developer can choose implementation sources without repeating the research.

## Commit
`git commit -m "lap 1: verify agricultural data sources"`
