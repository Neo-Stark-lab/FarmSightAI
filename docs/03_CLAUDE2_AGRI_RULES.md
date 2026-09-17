# Lap 2 — Claude 2: Agricultural Intelligence

## Mission
Convert agricultural knowledge into conservative, machine-readable rules.

## Input
Pull latest `main`, then read:
- `00_MASTER_CONTEXT.md`
- `docs/data-sources.md`
- `docs/ml-contract.md`

## Crops
Develop rules for:
- Rice
- Groundnut
- Maize

## Define
For each crop:
- growth stages
- approximate stage timing
- water sensitivity
- water-stress indicators
- rainfall considerations
- temperature considerations
- vegetation indicators
- conservative irrigation decision rules

## Rule Structure
Each rule should specify:
- condition
- evidence
- interpretation
- recommended action
- alternative action
- uncertainty

Example:
IF low soil moisture + declining vegetation moisture indicator + rainfall deficit
THEN increase water-stress risk.

ACTION:
Prioritize field verification and irrigation assessment.

## Recommendations
Use conditional language:
- consider
- prioritize checking
- reassess
- monitor
- verify in the field

Do not prescribe unsupported exact irrigation quantities.

## Output
Create:
`docs/agricultural-rules.md`

If useful, add rules under the existing backend/ML structure.

## Do Not
- Train ML
- Build frontend
- Invent field measurements
- Redesign the API

## Acceptance
The inference layer can consume the rules programmatically.

## Commit
`git commit -m "lap 2: add agricultural intelligence rules"`
