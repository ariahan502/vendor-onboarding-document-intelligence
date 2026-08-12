# Local Run

## Goal

Run the current project locally with:

- PostgreSQL
- FastAPI backend
- Next.js frontend

This setup is meant for early development and UI/API iteration, not production deployment.

## 1. Current services

The local stack includes:

- `postgres` on port `5432`
- `backend` on port `8000`
- `frontend` on port `3000`

## 2. Start with Docker Compose

From the repo root:

```bash
docker compose up --build
```

Expected local URLs:

- frontend: `http://localhost:3000`
- backend health: `http://localhost:8000/api/health`
- package queue API: `http://localhost:8000/api/packages/`

## 3. Current behavior

Right now:

- PostgreSQL starts as infrastructure
- backend serves FastAPI routes
- frontend renders queue and packet review pages
- package data is persisted in PostgreSQL or the configured local SQLite database
- uploaded PDFs use the local storage adapter by default

That means the stack is useful for:

- page development
- API contract iteration
- UI review

It is not a production deployment: use [DEPLOYMENT.md](/Users/hanlingjuan/Documents/vendor-onboarding-project/DEPLOYMENT.md)
for the managed database, Blob Storage, and secret-management boundary.

## 4. Backend notes

The backend container uses:

- `backend/Dockerfile`
- `backend/requirements.txt`
- `uvicorn app.main:app --reload`

The database URL inside Docker is:

`postgresql+psycopg://postgres:postgres@postgres:5432/vendor_onboarding`

For local non-Docker development, the backend now defaults to:

`sqlite+pysqlite:///./dev.db`

## 5. Frontend notes

The frontend container uses:

- `frontend/Dockerfile`
- `frontend/package.json`
- Next.js dev server on port `3000`

The frontend points to:

`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api`

## 6. What is still external to this repository

The application and production deployment contract are implemented. The following
steps require access to your cloud account and are deliberately not performed by
the repository:

- provisioning the Azure subscription resources described in [DEPLOYMENT.md](/Users/hanlingjuan/Documents/vendor-onboarding-project/DEPLOYMENT.md)
- configuring Entra application registrations and production secrets
- supplying a production Azure Document Intelligence resource for OCR

## 6.1 Optional Azure OCR for scanned PDFs

Text-based PDFs are parsed locally. For scanned PDFs, configure Azure AI Document
Intelligence by adding these values to `backend/.env`:

```bash
DOCUMENT_INTELLIGENCE_ENDPOINT=https://<resource-name>.cognitiveservices.azure.com/
DOCUMENT_INTELLIGENCE_API_KEY=<resource-key>
```

The service uses Azure's `prebuilt-read` model only when both values are present.
Without them, scanned documents remain in `OCR required` status and receive a
review finding instead of fabricated fields.

## 6.2 Identity, roles, and audit export

Local development uses the configured `DEVELOPMENT_ACTOR_ID` and
`DEVELOPMENT_ACTOR_ROLE` defaults so local development works without a login page. In a
protected environment, set `AUTH_REQUIRED=true`, `ENTRA_TENANT_ID`, and
`ENTRA_API_AUDIENCE`. The frontend obtains a Microsoft Entra access token and the
API validates its signature, issuer, audience, and assigned application role.
Accepted roles are `intake`, `reviewer`, and `admin`.

The MVP does not implement passwords or maintain its own identity provider.
Microsoft Entra ID is the identity provider. An API gateway is optional as an
additional network boundary, not a source of trusted actor headers.

Admins can export the append-only audit ledger at:

```text
GET /api/audit-events/export
```

Each event carries the previous event hash and its own hash. Store exports outside
the application database for long-term retention and independent verification.

## 6.3 Run the MVP evaluation suite

Run the deterministic evaluation suite from the project root:

```bash
make evaluate
```

It creates temporary PDFs and a temporary SQLite database, then verifies the
missing-insurance, legal-name mismatch, missing-tax-ID, and OCR-required cases.
It does not modify the local development queue or send documents to Azure.

## 6.4 Run queued processing locally

New packets enter `processing` with queued ingestion/OCR runs. Process one queued
packet from a separate terminal with:

```bash
make worker-once
```

For continuous processing, run `python backend/scripts/run_worker.py` with the
same `PYTHONPATH` environment used by the backend. Docker Compose starts the worker
service automatically.

These are the local processing commands.

## 7. Policy governance workflow

Admins can create a draft policy revision at
`POST /api/policy-rules/{rule_id}/revisions`. Record its regression scores using
`POST /api/policy-rules/{rule_id}/revisions/{revision_id}/evaluate`, then activate
only a passing revision through `POST /api/policy-rules/{rule_id}/revisions/{revision_id}/activate`.
All four scores must be at least `0.95`; each stage is appended to the audit ledger.

## 8. Database initialization options

### Option A. Preferred: Alembic migration

From inside the backend container or backend directory:

```bash
alembic upgrade head
```

### Option B. Fast local bootstrap: metadata create

```bash
python scripts/init_db.py
```

Use this only for quick local iteration. Alembic should remain the primary schema evolution path.

### Option C. Fastest no-Docker path

If Docker or local Postgres is unavailable, you can still run the backend against SQLite:

1. use the default `DATABASE_URL` from `backend/.env.example`
2. run:

```bash
python scripts/init_db.py
python scripts/seed_demo_data.py
python scripts/smoke_test_api.py
```

This is enough to validate:

- schema creation
- seed loading
- queue and packet detail API behavior
