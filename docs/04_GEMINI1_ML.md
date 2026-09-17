# Lap 3 — Gemini Pro 1: Water-Stress ML

## Mission
Design and implement the ML intelligence for FarmSight's core feature.

## Input
Pull latest `main`, then read:
- `00_MASTER_CONTEXT.md`
- `docs/data-sources.md`
- `docs/agricultural-rules.md`
- `docs/ml-contract.md`

## Problem
Estimate zone-level water-stress risk.

## Candidate Features
Evaluate:
- NDVI
- NDVI change
- NDMI
- NDMI change
- rainfall 7d
- rainfall 30d
- rainfall anomaly
- temperature
- temperature anomaly
- soil moisture
- soil-moisture change
- crop
- crop stage
- historical deviation
- context-filtered nearby-field deviation

## Model
Compare appropriate approaches such as:
- Logistic Regression baseline
- Random Forest
- XGBoost

Choose based on actual available data and explain the choice.

## Ground Truth
Document the actual target/label strategy.

If field labels are unavailable:
- do not fabricate labels
- use a clearly defined proxy only if appropriate
- document limitations
- never present proxy performance as real-world field accuracy

## Output
Inference should return:
- risk
- probability where justified
- confidence
- contributing factors
- model version

## Explainability
Provide feature contributions where practical. SHAP may be used.

## Missing/Stale Data
Document and implement behavior for:
- missing satellite
- stale satellite
- missing weather
- missing soil moisture

## Output Files
Create/update:
- `ml/`
- `docs/ml-design.md`

## Do Not
- Fabricate accuracy
- Build the frontend
- Redesign the API unnecessarily

## Acceptance
The ML module accepts the agreed feature schema and returns the documented prediction object.

## Commit
`git commit -m "lap 3: implement water stress intelligence"`
