# FarmSight AI — AgriThon 2026 AI Lap Plan

## Goal
Build FarmSight AI through a controlled multi-AI GitHub workflow.

FarmSight is an Explainable Digital Farm Twin for small and marginal farmers in Tamil Nadu.

**Tagline:** “See the problem. Understand why. Know what to do.”

## Core Feature
Water-stress and irrigation intelligence is the deeply implemented feature.

Supporting capabilities:
- crop health
- soil/nutrient stress risk
- pest/disease risk
- climate
- digital farm zones
- explainable advisory

## Lap Flow

```text
Existing Repo
    |
    v
Lap 0 — Go 1
Architecture + contracts
    |
    +----> Lap 1 — Claude 1: Data sources
    |
    +----> Lap 2 — Claude 2: Agricultural rules
    |
    +----> Lap 3 — Gemini 1: ML
                 |
                 v
        Lap 4 — Go 2: Data pipeline
                 |
        +--------+--------+
        v                 v
Lap 5 — Gemini 2     Lap 6 — Claude 3
Frontend             Explainability
        +--------+--------+
                 |
                 v
        Lap 7 — Go 1
        Full integration
                 |
                 v
        Lap 8 — Go 3
        QA + fixes
                 |
                 v
        Lap 9 — Claude 4
        Pitch + demo
```

## 15-Hour Plan

### Hour 0–1
Go 1: architecture and contracts.

### Hour 1–2
Claude 1 + Claude 2 + Gemini 1 in parallel.

### Hour 2–6
Go 2: data pipeline.
Gemini 2: frontend.

### Hour 4–6
Claude 3: explainability.

### Hour 6–9
Go 1: full integration.

### Hour 8–11
Go 3: QA and fixes.

### Hour 10–12
Critical bug fixing.

### Hour 11–13
Claude 4: pitch/demo.

### Hour 13–14
Full rehearsal.

### Hour 14–15
Final fixes and freeze.

## Critical Rule
Every AI must work on the existing GitHub repository and own only its assigned scope.

Do not tell multiple AIs to “build the whole project.”

## Git Pattern

```bash
git pull origin main
git checkout -b lap/XX-name

# perform assigned work

git add .
git commit -m "lap XX: description"
git push -u origin lap/XX-name
```

Then review and merge before dependent work begins.

## Scientific Guardrails
Never:
- claim satellite directly measures exact NPK without validation
- call satellite data real-time
- claim exact irrigation quantities from satellite alone
- fabricate model accuracy
- treat confidence as guaranteed correctness

## Final User Journey

```text
Farmer
  ↓
Location + Boundary + Crop + Sowing Date
  ↓
Digital Farm Twin
  ↓
Zones
  ↓
What Needs Attention?
  ↓
Water-Stress Risk
  ↓
Why?
  ↓
Satellite + Weather + Soil-Moisture Evidence
  ↓
Confidence + Data Freshness
  ↓
Recommended Action
```

## Definition of Done
The final prototype must support the complete journey and remain honest about data limitations and uncertainty.
