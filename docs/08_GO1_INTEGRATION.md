# Lap 7 — ChatGPT Go 1: Full Integration

## Mission
Integrate the completed modules into one working application.

## Input
Pull latest `main`.

Read:
- all docs relevant to the system
- frontend
- backend
- ML
- data
- tests

## Integrate
Connect:
Frontend
→ FastAPI
→ farm/database
→ data pipeline
→ ML
→ agricultural rules
→ explainability
→ recommendation
→ frontend

## Required Farmer Flow
1. Location
2. Boundary
3. Crop
4. Sowing date
5. Crop-stage calculation
6. Zone generation
7. Data collection/load
8. Feature calculation
9. ML prediction
10. Rule contextualization
11. Explanation
12. Recommendation
13. Frontend display

## Reliability
Provide a fallback sample-data mode if external services are unreliable.

Clearly label sample/demo data.

## Error Handling
Gracefully handle:
- unavailable satellite
- unavailable weather
- unavailable soil moisture
- model failure
- malformed polygon
- missing inputs
- database failure

## Testing
Add integration tests for the core farmer journey.

## Acceptance
A fresh clone can run the application using documented setup instructions and the core journey works end-to-end.

## Do Not
Do not rewrite working modules just for stylistic reasons.

## Commit
`git commit -m "lap 7: integrate FarmSight end to end"`
