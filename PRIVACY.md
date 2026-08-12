# Privacy and Sample Data Policy

## Public repository rule

This repository contains only synthetic sample data.
Do not add real vendor onboarding packets or any document containing personal,
financial, tax, banking, contract, insurance, or confidential business information.

In particular, never commit:

- real W-9s, tax IDs, bank forms, signatures, contracts, or certificates
- names, addresses, email addresses, or phone numbers from real people or vendors
- screenshots, logs, database exports, or audit exports that contain such information
- cloud credentials, database URLs, OAuth client secrets, or storage connection strings

## Safe sample-data practice

Use fictional vendors and deliberately fake identifiers. A reviewer should be able to
understand the workflow from the example without being able to identify a real person
or organisation. The tracked PDFs in `frontend/public/sample-documents/` are synthetic
ABC placeholders for this reason.

For public access, accept only the bundled sample files, or reset uploaded documents
and database records after each test session. Do not let anonymous visitors upload
documents to an individually managed cloud account.

## Azure processing boundary

When Azure Document Intelligence is enabled, document contents and extraction results
are sent to that Azure service for analysis. It should therefore be enabled only for
synthetic sample-data environments or with an organisation's approved data-processing agreement. Azure
states that analysis data/results are stored temporarily to return results and can be
deleted after retrieval; review the service's current regional, retention, and
compliance terms before using real data.

## Before publishing

1. Run `git status --ignored` and check that no `.env`, database, upload directory, or
   local dependency directory is staged.
2. Review PDF files, images, logs, and screenshots manually.
3. Rotate any cloud credential that was ever pasted into a terminal, issue tracker, or
   committed file.
4. Keep the public repository free of deployment secret values; use placeholders only.
