# Lap 5 — Gemini Pro 2: Frontend

## Mission
Build the farmer-facing FarmSight interface.

## Input
Pull latest `main`, then read:
- `00_MASTER_CONTEXT.md`
- `docs/architecture.md`
- `docs/api-contract.md`

Inspect the existing frontend first.

## Required Screens
### Landing
Message:
“Understand your farm before the problem becomes serious.”

### Farm Setup
- location
- farm boundary
- crop
- sowing date

### Farm Twin
- interactive map
- boundary
- zones
- layer controls

### What Needs Attention?
Show:
- highest-priority zones
- water-stress status
- crop-health status
- confidence

### Zone Detail
Show:
- risk
- confidence
- Why?
- evidence
- data freshness
- recommendation
- alternatives

## Evidence
Do not display only generated prose.
Show actual feature/evidence values and observation dates when available.

## States
Implement:
- loading
- empty
- missing data
- stale data
- API failure
- no-risk state

## Do Not
- Implement ML
- Invent final API contracts
- Fabricate real observations
- Redesign backend

## Acceptance
A user can navigate from setup → map → zone → explanation → action.

## Commit
`git commit -m "lap 5: build FarmSight farmer interface"`
