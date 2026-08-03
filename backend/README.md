# Backend

This folder now contains the first implementation scaffold for:

- FastAPI application startup
- API routing
- SQLAlchemy base and session setup
- domain models aligned to `schema.sql`

Core package layout:

- `app/main.py`
- `app/api/`
- `app/db/`
- `app/models/`
- `app/config.py`

Next implementation steps:

- connect package queue and packet detail endpoints to the database
- add seed-loading scripts
- replace sample service data with SQLAlchemy-backed queries

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
