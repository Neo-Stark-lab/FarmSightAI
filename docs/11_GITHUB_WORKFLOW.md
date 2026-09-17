# FarmSight AI — GitHub Workflow

## Single Source of Truth
GitHub is the authoritative project state.

Do not pass the whole project manually between AI accounts.

## Before Every Lap
Run:
```bash
git pull origin main
```

Then inspect the repository and read:
- `00_MASTER_CONTEXT.md`
- current lap instructions
- relevant previous documentation

## Branches
Use:
- `lap/01-data-sources`
- `lap/02-agri-rules`
- `lap/03-ml`
- `lap/04-data-pipeline`
- `lap/05-frontend`
- `lap/06-explainability`
- `lap/07-integration`
- `lap/08-qa`
- `lap/09-demo`

Lap 0 may use a foundation branch such as `lap/00-architecture`.

## Commit
Example:
```bash
git add .
git commit -m "lap 03: implement water stress intelligence"
git push -u origin lap/03-ml
```

## Merge
Project owner reviews and merges completed branches into `main`.

Dependent laps start only after required work is merged.

## Rules
- Do not overwrite other AI work.
- Do not rebuild unrelated modules.
- Do not silently change API contracts.
- Update API docs when contracts change.
- Document new dependencies.
- Never commit secrets.
- Use `.env.example`, never commit `.env`.

## Handoff
Every AI must report:
1. What changed
2. Files changed
3. How to run
4. Tests performed
5. Known limitations
6. Next AI's starting point

## Parallelization
After Lap 0:
- Claude 1, Claude 2 and Gemini 1 can work in parallel.
- Go 2 and Gemini 2 can overlap once their required contracts are available.
- Claude 3 can work from the ML/data contracts.
- Go 1 integration starts after the required modules are merged.
- Go 3 follows the first runnable integration.
- Claude 4 should finalize the story after the product is stable.
