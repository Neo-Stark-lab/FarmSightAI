# Lap 8 — ChatGPT Go 3: Integration QA

## Mission
Act as an independent QA/integration engineer.

Do not rebuild the project.

## Input
Pull latest `main` and run the actual application.

Read all relevant docs.

## Functional Tests
Test:
- landing
- farm setup
- location
- boundary
- crop
- sowing date
- map
- zones
- analysis
- explanation
- recommendation

## API Tests
Test:
- valid requests
- invalid requests
- missing parameters
- malformed polygons
- empty responses
- API failures

## Data Tests
Test:
- missing satellite
- stale satellite
- missing weather
- missing soil moisture
- incomplete historical data

## ML Tests
Test:
- valid feature vector
- missing feature
- unexpected feature
- model unavailable
- inference failure

## Frontend Tests
Check:
- loading
- errors
- empty state
- mobile layout
- map rendering
- zone selection
- evidence
- confidence

## Scientific Audit
Flag:
- unsupported exact NPK claims
- “real-time satellite” claims
- unsupported exact irrigation quantities
- fabricated accuracy
- confidence described as guaranteed correctness

## Output
Create:
`docs/qa-report.md`

For every issue:
- severity
- location
- problem
- reproduction
- recommended fix
- status

Fix critical/blocking issues directly when safe.

## Acceptance
No critical issue remains in the core farmer journey.

## Commit
`git commit -m "lap 8: complete integration QA and fixes"`
