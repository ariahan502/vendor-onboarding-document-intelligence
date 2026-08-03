# Production Deployment Boundary

## What This Project Can Deploy

The repository contains a production runtime contract, not a claim that a cloud
environment has already been provisioned. It removes the two unsafe local defaults:
SQLite and a container-local upload directory.

Use these managed Azure resources for a production-like deployment:

- Azure Container Apps: `frontend`, `backend`, and `worker`
- Azure Database for PostgreSQL Flexible Server: application database
- Azure Blob Storage: private `vendor-documents` container
- Azure Key Vault: database URL, storage connection string, OCR key
- Microsoft Entra ID or an API gateway: authenticates users and forwards trusted
  `X-Actor-ID` and `X-Actor-Role` headers

The application does not create these resources automatically. That requires an
Azure subscription with the correct tenant and billing access.

## Required Production Secrets

Store these in Key Vault or the managed runtime's secret store. Do not commit them.

```text
DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>:5432/<database>?sslmode=require
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_STORAGE_CONTAINER=vendor-documents
CORS_ORIGINS=https://<frontend-domain>
DOCUMENT_INTELLIGENCE_ENDPOINT=https://<resource>.cognitiveservices.azure.com/
DOCUMENT_INTELLIGENCE_API_KEY=<optional-until-OCR-is-enabled>
```

Set these non-secret environment values:

```text
ENVIRONMENT=production
STORAGE_BACKEND=azure_blob
AUTH_REQUIRED=true
```

## Deployment Order

1. Provision the managed database, private blob container, secrets, and identity gateway.
2. Build and deploy the backend image, then run `alembic upgrade head` as a one-off job.
3. Deploy the worker with the same database and storage configuration as the backend.
4. Deploy the frontend with `NEXT_PUBLIC_API_BASE_URL` pointing at the protected API.
5. Check `GET /api/health/ready`; it verifies database connectivity and storage availability.
6. Upload a non-sensitive test packet, review it, and confirm the audit export is retained outside the application database.

## Compose Reference

For a controlled, self-hosted environment, create an untracked `.env.production`
with the required values and run:

```bash
docker compose -f docker-compose.production.yml run --rm migrate
docker compose -f docker-compose.production.yml up --build -d
```

This is a runtime reference only. A managed Azure deployment should use the same
variables through Key Vault and managed identity rather than copying secrets into a file.

## Explicit Restrictions

- Blob storage is private; documents are served only through the application API.
- The current trusted-header role model requires an authenticated proxy. Directly
  exposing the API without that proxy would allow callers to forge actor headers.
- Audit hashes detect changes to an exported ledger, but exports still need external
  retention and access controls for regulatory-grade immutability.
- OCR validation remains blocked until an Azure Document Intelligence resource can be accessed.
