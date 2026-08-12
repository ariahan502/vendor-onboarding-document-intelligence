# Frontend

This folder contains the reviewer workflow UI for:

- package queue
- packet review workspace
- findings and evidence display
- decision actions and review history

Current structure:

- `app/` for Next.js App Router pages
- `components/` for UI pieces
- `lib/` for API and shared helpers
- `types/` for API contract types

The UI is connected to the backend package queue and review APIs. When Entra
configuration is supplied, it obtains an access token for the API and the backend
validates that token and its application role. API Management remains an optional
additional production boundary.

Local container setup now exists via:

- [frontend/Dockerfile](/Users/hanlingjuan/Documents/vendor-onboarding-project/frontend/Dockerfile)
- [docker-compose.yml](/Users/hanlingjuan/Documents/vendor-onboarding-project/docker-compose.yml)
- [LOCAL_RUN.md](/Users/hanlingjuan/Documents/vendor-onboarding-project/LOCAL_RUN.md)

The PDFs under `public/sample-documents/` are synthetic placeholders only. See
[PRIVACY.md](/Users/hanlingjuan/Documents/vendor-onboarding-project/PRIVACY.md).
