# FarmSight AI — Master Context

## Project
**FarmSight AI — Explainable Digital Farm Twin for Small & Marginal Farmers**

Tagline: **“See the problem. Understand why. Know what to do.”**

## Target
- Tamil Nadu
- Small and marginal farmers
- Web application
- Crops: Rice, Groundnut, Maize
- No physical sensors in the prototype

## Farmer Inputs
1. Location
2. Farm boundary
3. Crop
4. Sowing date

The system estimates crop growth stage from the sowing date.

## Core Feature
The deeply implemented feature is **zone-level water-stress and irrigation intelligence**.

Supporting layers:
- Crop health
- Soil/nutrient stress risk
- Pest/disease risk
- Climate
- Farm zones

## Data
Use practical free/open data suitable for a hackathon:
- Sentinel-2 / remote sensing
- ISRO/Bhoonidhi
- NISAR soil-moisture products where practically accessible
- Weather APIs
- NASA POWER
- Tamil Nadu agricultural datasets
- Historical observations

Do not claim a source provides information it does not actually provide.

## Scientific Guardrails
- Do not claim satellite directly measures exact N, P, K unless validated ground data supports it.
- Prefer terms such as **nutrient-stress risk** or **soil-condition indicator**.
- Do not call satellite observations “real-time”.
- Say observations are updated when new data becomes available.
- Do not claim exact irrigation quantities from satellite alone.
- Do not fabricate model accuracy.
- Ground truth limitations must be documented.

## Core Water-Stress Features
Potential features:
- NDVI
- NDVI temporal change
- NDMI
- NDMI temporal change
- rainfall 7d / 30d
- rainfall anomaly
- temperature
- temperature anomaly
- soil moisture
- soil-moisture change
- crop
- crop stage
- historical deviation
- filtered nearby-field deviation

## Output
For every zone, expose:
- water-stress risk
- probability only where justified
- confidence
- contributing factors
- evidence
- data freshness

**Confidence is model/data confidence, not a guarantee of correctness.**

## Recommendations
Recommendations must be conservative and conditional.

Example:
> Prioritize checking this zone and consider irrigation based on local field conditions.

If rainfall is expected:
> Reassess before irrigating.

If uncertainty is high:
> Field verification is recommended.

## Digital Farm Twin
Represent the farm as meaningful zones. Each zone can contain:
- health status
- water-stress risk
- evidence
- confidence
- recommendation

## Primary UX
**Farm Map → What Needs Attention? → Zone → Why? → Evidence → Action**

## Technical Direction
Preferred stack:
- React + Vite + TypeScript
- Tailwind CSS
- Leaflet or MapLibre
- FastAPI
- PostgreSQL/PostGIS where practical
- Python
- pandas/numpy/geopandas/rasterio
- scikit-learn/XGBoost where justified
- SHAP where useful

## GitHub Rule
GitHub is the single source of truth.

Every AI must:
1. Pull the latest repository.
2. Inspect the existing structure.
3. Read this file.
4. Read relevant lap instructions.
5. Modify only its assigned scope.
6. Test its work.
7. Commit and push its branch.
8. Provide a concise handoff.

Do not rebuild unrelated modules.

## Ownership
- Go 1: Architecture + final integration
- Claude 1: Data-source verification
- Claude 2: Agricultural rules
- Gemini 1: ML
- Go 2: Data pipeline
- Gemini 2: Frontend
- Claude 3: Explainability/uncertainty
- Go 3: QA
- Claude 4: Pitch/demo

## Definition of Done
A farmer can:
1. Enter/select a location.
2. Define/edit a boundary.
3. Select crop.
4. Enter sowing date.
5. View the farm map.
6. See meaningful zones.
7. See water-stress risk.
8. Open a zone.
9. Understand why it was flagged.
10. See evidence and freshness.
11. Receive a conservative action.
12. Understand uncertainty.
