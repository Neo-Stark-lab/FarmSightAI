# Lap 0 — ChatGPT Go 1: Technical Architecture

## Mission
Create the technical foundation. This is **not** the final integration pass.

## Input
- Existing GitHub repository
- `00_MASTER_CONTEXT.md`
- Existing folder structure

## Tasks
1. Pull and inspect the repository.
2. Preserve the existing structure unless a concrete reason requires change.
3. Define module boundaries.
4. Define data models.
5. Define API contracts.
6. Define ML input/output contracts.
7. Define integration conventions.
8. Define environment-variable conventions.

## Data Models
Define schemas for:
- Farm
- Zone
- Observation
- Feature set
- Prediction
- Evidence
- Recommendation

Include timestamps, source, freshness and model version where appropriate.

## API
Define contracts for the core farmer journey, such as:
- farm creation
- farm retrieval
- farm analysis
- zone retrieval
- zone detail
- recommendation

Use the existing backend structure if already present.

## ML Contract
Define the expected feature schema and prediction schema. Do not create fake data or accuracy.

## Output
Create/update:
- `docs/architecture.md`
- `docs/api-contract.md`
- `docs/data-model.md`
- `docs/ml-contract.md`

Only implement foundational code needed by the contracts.

## Do Not
- Build the complete frontend
- Train the ML model
- Research datasets
- Invent agricultural rules
- Fabricate accuracy
- Rewrite unrelated existing code

## Acceptance
Another AI can implement the data pipeline, ML and frontend without guessing interfaces.

## Commit
`git commit -m "lap 0: establish architecture and contracts"`
