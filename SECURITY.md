# Security Policy

## Scope

Treat all uploaded content as sensitive by default. Do not process real vendor
documents without an approved operating, retention, and access model.

## Secret handling

The repository ignores local environment files, local SQLite databases, upload
directories, PostgreSQL volumes, and the optional `backend/.vendor/` dependency
directory. Keep real values only in an untracked environment file locally or in Azure
Key Vault for a controlled deployment.

Never commit values for:

- `DATABASE_URL`
- `AZURE_STORAGE_CONNECTION_STRING`
- `DOCUMENT_INTELLIGENCE_API_KEY`
- OAuth/Entra client secrets, certificates, tokens, or API keys

If a secret is committed, rotate it immediately. Removing it from a later commit does
not remove it from Git history.

## Deployment requirements

A real deployment must:

- keep Blob containers private and serve files through the authenticated application
- use TLS, a managed PostgreSQL database, Key Vault, and a restricted backend network boundary
- validate Entra-issued access tokens and application roles at the backend; optionally use API
  Management for perimeter controls
- restrict the service to synthetic sample data unless the data owner has approved the
  processing, retention, and access model

The frontend implements Entra sign-in. Do not expose the production configuration to
anonymous public users.

## Reporting a vulnerability

Do not file public issues containing credentials or sensitive documents. If this is
your repository, use GitHub private reporting if configured, or contact the repository
owner privately with a minimal reproduction and no sensitive payloads.
