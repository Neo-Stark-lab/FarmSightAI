# Lap 6 — Claude 3: Explainability and Uncertainty

## Mission
Make AI outputs understandable and scientifically honest.

## Input
Pull latest `main`, then read:
- `00_MASTER_CONTEXT.md`
- `docs/ml-design.md`
- `docs/agricultural-rules.md`
- `docs/data-pipeline.md`

## Separate
### Risk
Severity of the detected condition.

### Confidence
Model/data confidence.

### Data Quality
Freshness and completeness of observations.

Never merge these into one misleading score.

## Explanation
Every alert should answer:
1. What was detected?
2. Where?
3. Why does the system think this?
4. What evidence supports it?
5. How fresh is the evidence?
6. What should the farmer consider?
7. What uncertainty remains?

## Multiple Causes
If several causes are plausible, rank them by evidence strength and state uncertainty.

## Stale Data
Show age, explain limitations and reduce confidence where appropriate.

## Output
Create/update:
- `docs/explainability.md`
- `docs/uncertainty.md`

Implement only explainability-related changes.

## Acceptance
A farmer can understand why a zone was flagged without relying on a black-box statement.

## Commit
`git commit -m "lap 6: add explainability and uncertainty handling"`
