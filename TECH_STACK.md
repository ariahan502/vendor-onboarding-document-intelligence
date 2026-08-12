# Tech Stack

## Goal

Choose a practical, production-oriented stack for `Vendor Onboarding Document Intelligence`.

The stack should optimize for:

- fast iteration
- clean architecture
- clear operability
- realistic document workflow support
- easy local development
- room for evaluation and future expansion

It should not optimize for:

- maximum novelty
- premature scalability
- heavy enterprise integration in v1

## 1. Recommended stack

### Frontend

- `Next.js`
- `TypeScript`
- `Tailwind CSS`
- `shadcn/ui` or similar component primitives
- `react-pdf` or a similar PDF viewer layer

Why:

- strong ecosystem
- easy dashboard and reviewer UI construction
- fast iteration on internal-tool style interfaces
- good fit for three-panel review workspace

### Backend

- `FastAPI`
- `Python 3.11+`
- `Pydantic`
- `SQLAlchemy` or `SQLModel`
- `Alembic`

Why:

- Python is the easiest place to implement document extraction, normalization, evaluation, and rule logic
- FastAPI is clean for structured APIs
- strong fit for AI/data workflow code

### Database

- `PostgreSQL`

Why:

- strong relational modeling for packages, documents, fields, findings, and decisions
- good fit for auditability and reproducibility
- enough for MVP without overcomplication

### Async jobs

- `Celery` or `RQ`
- `Redis`

Why:

- OCR, parsing, extraction, and evaluation runs should not block request/response flows
- easy to model processing jobs and retries

For the earliest MVP, even a lighter background-task pattern is acceptable, but Redis-backed jobs are the more realistic medium-term choice.

### File storage

- local filesystem in development
- abstract storage interface for future S3-compatible storage

Why:

- simplest local development path
- keeps architecture clean for later expansion

### OCR and document parsing

- `PyMuPDF` for PDF parsing and page access
- `pytesseract` or cloud OCR later if needed
- optional layout-aware parser later

Why:

- enough to get started
- lets us separate document processing from business logic

### AI / extraction layer

- schema-based extraction with LLM structured outputs
- deterministic parsing where possible
- prompt versioning in database

Why:

- contracts and insurance docs are not fixed enough for rules alone
- structured outputs keep the system bounded

### Rules and decision layer

- custom Python rule engine for MVP

Why:

- policy rules are simple enough that a full external rules platform is unnecessary
- clearer for interviews and easier to control

### Evaluation layer

- Python evaluation runner
- Postgres tables for cases and runs
- notebook optional for analysis only
- simple dashboard or admin tables for metrics

Why:

- evaluation is a first-class part of the project
- we want versioned, repeatable runs

### Dev environment

- `Docker Compose`
- `.env` configuration
- `Makefile` or package scripts

Why:

- makes local setup easier
- keeps the project easy to run locally

## 2. Architecture shape

The recommended architecture is:

- `frontend`
- `backend api`
- `worker`
- `postgres`
- `redis`
- `document storage`

High-level flow:

1. frontend uploads packet
2. backend creates package and document records
3. worker runs OCR and extraction
4. backend stores normalized fields and findings
5. decision engine produces recommendation
6. reviewer confirms or overrides in frontend
7. evaluation runner benchmarks system versions separately

## 3. What we should avoid in v1

Avoid these unless a clear need appears:

- microservices
- Kubernetes
- vector database as a core dependency
- LangGraph-style heavy workflow frameworks
- multi-agent orchestration frameworks
- full event streaming architecture
- complicated enterprise auth
- large cloud infra setup

These would add complexity faster than value for this project.

## 4. Minimum viable screens

The stack should support these screens well.

### 4.1 Package queue

Shows:

- vendor name
- packet status
- missing document indicators
- review priority
- recommendation status

### 4.2 Packet review workspace

Three-panel layout:

- left: document list
- center: PDF viewer
- right: extracted fields, findings, and decision actions

### 4.3 Findings and evidence

Shows:

- mismatch findings
- policy violations
- confidence warnings
- source pages and evidence snippets

### 4.4 Evaluation or admin view

Shows:

- extraction metrics
- finding accuracy
- routing accuracy
- benchmark runs by version

## 5. Recommended repository structure

One clean monorepo is the best default.

Suggested layout:

```text
vendor-onboarding-project/
  frontend/
  backend/
  worker/
  migrations/
  docs/
  seeds/
  scripts/
  docker-compose.yml
```

Alternative:

- combine `backend` and `worker` in one Python app package at first

That is often simpler for MVP.

## 6. Data and model boundaries

Keep these boundaries explicit:

### Backend owns

- package lifecycle
- document metadata
- extraction records
- normalized values
- comparison logic
- findings
- decisions
- evaluation

### Frontend owns

- review workflow UI
- evidence presentation
- reviewer actions
- filters and review ergonomics

### Worker owns

- OCR
- extraction jobs
- normalization pipeline
- comparison pipeline
- policy checks
- scheduled evaluation runs

## 7. LLM usage boundaries

Use LLMs only where they add clear value.

Good uses:

- structured field extraction from messy text
- interpreting ambiguous payment-term language
- evidence-grounded explanation generation
- fuzzy entity resolution support

Bad uses:

- deciding deterministic policy thresholds
- replacing schema validation
- replacing audit trails
- free-form end-to-end approval decisions

## 8. Suggested versions of ambition

### Version A. Strong MVP

- Next.js frontend
- FastAPI backend
- Postgres
- local file storage
- simple worker
- OCR + structured extraction
- rule-based findings
- reviewer UI

This is the recommended starting point.

### Version B. Production-oriented build

Add:

- Redis-backed jobs
- richer evidence model
- evaluation dashboard
- benchmark version tracking
- better UI polish

### Version C. Overbuilt version to avoid early

Avoid starting here:

- multiple services
- many connectors
- agent orchestration frameworks
- vector retrieval stack everywhere
- generalized workflow platform

## 9. My recommendation

If we want the safest, strongest, most teachable stack:

- `Next.js + TypeScript + Tailwind` for frontend
- `FastAPI + Python + Postgres` for backend
- `Redis + worker` for async processing
- `PyMuPDF + OCR tooling` for document parsing
- custom normalization, comparison, rules, and evaluation logic

This gives us:

- realistic engineering structure
- strong AI/data implementation ergonomics
- a good reviewer UI
- enough complexity to feel real
- not so much complexity that the project stalls

## 10. Next step

Now that we have:

- [PROJECT_PLAN.md](/Users/hanlingjuan/Documents/vendor-onboarding-project/PROJECT_PLAN.md)
- [BUILD_STRATEGY.md](/Users/hanlingjuan/Documents/vendor-onboarding-project/BUILD_STRATEGY.md)
- this stack choice

the next best step is to define:

- the required MVP screens
- the first schema version
- the rubric for evaluating open-source base candidates
