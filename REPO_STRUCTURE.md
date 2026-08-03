# Repo Structure

## Goal

Define a clean repository structure for `Vendor Onboarding Document Intelligence` so implementation can start without mixing product logic, document processing, and UI concerns together.

This structure is designed to support:

- a reviewer-facing frontend
- a Python backend API
- background document processing
- seed data and local demo setup
- future evaluation workflows

## 1. Recommended top-level layout

```text
vendor-onboarding-project/
  frontend/
  backend/
  worker/
  docs/
  seeds/
  scripts/
  PROJECT_PLAN.md
  BUILD_STRATEGY.md
  TECH_STACK.md
  MVP_SCREENS.md
  schema.sql
  SCHEMA_V1.md
  REPO_STRUCTURE.md
```

## 2. Folder purposes

### `frontend/`

Purpose:

- reviewer-facing application
- queue view
- packet review workspace
- findings, evidence, and decision UI

Suggested future contents:

- `app/`
- `components/`
- `lib/`
- `styles/`

### `backend/`

Purpose:

- API surface
- database models
- package workflow logic
- rules, findings, decisions

Suggested future contents:

- `app/main.py`
- `app/api/`
- `app/models/`
- `app/services/`
- `app/schemas/`
- `app/db/`

### `worker/`

Purpose:

- OCR jobs
- extraction jobs
- normalization jobs
- comparison jobs
- scheduled evaluation runs

Suggested future contents:

- `app/tasks/`
- `app/pipelines/`
- `app/runners/`

### `docs/`

Purpose:

- implementation-facing documentation
- architecture diagrams
- API notes
- design decisions

Recommended use:

- put future ADRs, architecture notes, and UI references here

### `seeds/`

Purpose:

- sample vendor packets
- fixture metadata
- labeled evaluation examples

Recommended use:

- synthetic demo packets for local development
- JSON or CSV metadata for expected findings and expected decisions

### `scripts/`

Purpose:

- local utilities
- dev setup helpers
- seed loaders
- evaluation runners

## 3. Why this split is useful

This split keeps the project understandable:

- `frontend` owns reviewer experience
- `backend` owns workflow and business state
- `worker` owns asynchronous document intelligence

That separation is strong enough to feel like a real system, but still simple enough for a portfolio project.

## 4. What not to do

Avoid these early repo mistakes:

- putting all logic into one giant notebook
- mixing OCR code directly into UI routes
- storing product rules only in frontend state
- burying business logic inside prompt text with no backend structure
- scattering sample data randomly around the repo

## 5. First implementation milestones

Once this structure exists, the best next implementation steps are:

1. add backend model files that mirror `schema.sql`
2. add seed packet examples under `seeds/`
3. create frontend route placeholders for queue and review workspace
4. create worker placeholders for OCR and extraction pipeline stages

## 6. Recommendation

This repo should begin as a clean monorepo with separate app areas, not as a pile of disconnected experiments.

That gives us:

- cleaner iteration
- clearer architecture story
- easier demo setup
- better portfolio quality
