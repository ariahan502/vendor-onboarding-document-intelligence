# Vendor Onboarding Document Intelligence

A document-review workflow for vendor onboarding packets. It helps procurement and
finance reviewers determine whether a packet can move forward, which information is
missing or inconsistent, and what source evidence supports the recommendation.

This is a portfolio project. It is designed around a bounded, auditable business
workflow rather than autonomous approval. It is **not** a live production service and
must not be used with real vendor, tax, banking, or contract data.

## What it does

- accepts a packet containing a contract, W-9, and insurance certificate
- extracts a fixed set of fields from text PDFs and records evidence
- safely routes scanned PDFs to OCR/manual review instead of fabricating values
- detects missing documents, missing tax IDs, and cross-document name mismatches
- keeps human reviewers in control of final decisions and requires explicit approval
  overrides for open high-risk findings
- preserves field corrections, finding resolutions, policy changes, and decisions in
  an append-only audit trail
- blocks policy activation until recorded regression scores meet the 0.95 threshold

## Architecture

```text
Next.js reviewer UI
        |
FastAPI API ---- PostgreSQL / SQLite (local)
        |                    |
        |                    +-- audit events, decisions, policy revisions
        +-- local files / Azure Blob Storage
        +-- optional Azure Document Intelligence OCR
        |
background worker ---- ingestion, OCR, extraction, validation
```

The intended cloud boundary is documented in [DEPLOYMENT.md](DEPLOYMENT.md). Microsoft
Entra sign-in is implemented through optional environment configuration; an API gateway
remains a recommended additional production boundary.

## Quick start

### Option 1: Docker Compose

```bash
docker compose up --build
```

Then open `http://localhost:3000`. The API health check is available at
`http://localhost:8000/api/health`.

### Option 2: Run the regression suite

The suite creates a temporary SQLite database and temporary synthetic PDFs. It never
modifies the local demo database or calls Azure.

```bash
python3 -m pip install -r backend/requirements.txt
PYTHONPATH=backend python backend/scripts/evaluate_mvp.py
```

After installing dependencies, `make evaluate` runs the same suite.

## Demo data and privacy

All files under `frontend/public/sample-documents/` are synthetic placeholders. Do not
commit or upload real W-9s, contracts, insurance certificates, tax IDs, bank details,
or employee/customer information. See [PRIVACY.md](PRIVACY.md) and
[SECURITY.md](SECURITY.md) before publishing or deploying.

## Quality checks

`make evaluate` verifies the main workflow controls:

- missing-insurance, name-mismatch, tax-ID-gap, and OCR-required cases
- approval override and finding-resolution behavior
- field-correction and audit-chain preservation
- background worker handoff and role guards
- policy revision evaluation, activation protection, and evaluation metrics
- production configuration guard

GitHub Actions runs this suite for pushes and pull requests.

## Repository guide

- [PROJECT_PLAN.md](PROJECT_PLAN.md) — product and architecture rationale
- [PROJECT_BACKLOG.md](PROJECT_BACKLOG.md) — completed MVP scope and release boundary
- [LOCAL_RUN.md](LOCAL_RUN.md) — local execution and Azure OCR configuration
- [DEPLOYMENT.md](DEPLOYMENT.md) — production/staging deployment contract
- [SCHEMA_V1.md](SCHEMA_V1.md) — data model notes

## Portfolio-safe deployment target

For a personal portfolio, the recommended endpoint is a short-lived, access-controlled
staging demo that uses only synthetic documents. Keep Azure credentials in Key Vault,
restrict API access behind Entra ID/API Management, set a spending budget, and delete
the resource group after recording a demo. Do not expose a public upload endpoint for
real documents.

## License

No license has been selected yet. Add an explicit license before accepting external
contributions or presenting the repository as reusable open-source software.
