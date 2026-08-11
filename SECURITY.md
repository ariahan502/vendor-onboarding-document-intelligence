# Security Policy

## Scope

This repository is a portfolio project, not a hosted service for processing real
vendor documents. Treat all uploaded content as sensitive by default.

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
- use TLS, a managed PostgreSQL database, Key Vault, and a trusted identity gateway
- keep the backend non-public behind an API gateway
- validate Entra-issued tokens at the gateway and set actor headers there, never from
  an untrusted browser request
- restrict the service to synthetic demo data unless the data owner has approved the
  processing, retention, and access model

The current frontend does not implement Entra sign-in. Do not expose the production
configuration to anonymous public users until that integration exists.

## Reporting a vulnerability

Do not file public issues containing credentials or sensitive documents. If this is
your repository, use GitHub private reporting if configured, or contact the repository
owner privately with a minimal reproduction and no sensitive payloads.
