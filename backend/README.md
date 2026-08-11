# Backend

This folder contains the FastAPI implementation for:

- FastAPI application startup
- API routing
- SQLAlchemy base and session setup
- domain models aligned to `schema.sql`
- document intake, storage, deterministic extraction, validation, and OCR fallback
- reviewer decisions, field corrections, finding resolutions, and audit export
- policy catalogue and evaluated policy-revision activation

Core package layout:

- `app/main.py`
- `app/api/`
- `app/db/`
- `app/models/`
- `app/config.py`

Run the deterministic regression suite from the repository root:

```bash
PYTHONPATH=backend python backend/scripts/evaluate_mvp.py
```

Database evolution now includes:

- [backend/alembic.ini](/Users/hanlingjuan/Documents/vendor-onboarding-project/backend/alembic.ini)
- [backend/alembic/env.py](/Users/hanlingjuan/Documents/vendor-onboarding-project/backend/alembic/env.py)
- [backend/alembic/versions/20260730_0001_initial_schema.py](/Users/hanlingjuan/Documents/vendor-onboarding-project/backend/alembic/versions/20260730_0001_initial_schema.py)
- [backend/scripts/init_db.py](/Users/hanlingjuan/Documents/vendor-onboarding-project/backend/scripts/init_db.py)
- [backend/scripts/seed_demo_data.py](/Users/hanlingjuan/Documents/vendor-onboarding-project/backend/scripts/seed_demo_data.py)
- [backend/scripts/smoke_test_api.py](/Users/hanlingjuan/Documents/vendor-onboarding-project/backend/scripts/smoke_test_api.py)

Local container setup now exists via:

- [backend/Dockerfile](/Users/hanlingjuan/Documents/vendor-onboarding-project/backend/Dockerfile)
- [docker-compose.yml](/Users/hanlingjuan/Documents/vendor-onboarding-project/docker-compose.yml)
- [LOCAL_RUN.md](/Users/hanlingjuan/Documents/vendor-onboarding-project/LOCAL_RUN.md)

For the public-repository data policy and deployment security requirements, see
[PRIVACY.md](/Users/hanlingjuan/Documents/vendor-onboarding-project/PRIVACY.md) and
[SECURITY.md](/Users/hanlingjuan/Documents/vendor-onboarding-project/SECURITY.md).
