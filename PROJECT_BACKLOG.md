# Vendor Onboarding Document Intelligence Backlog

This is the working ticket board for the MVP. Each ticket has a concrete outcome
and acceptance criteria so that work can be closed instead of remaining vague.

## Done

### T-001 Product and Data Contract

- Status: done
- Outcome: practical procurement problem, MVP boundaries, system plan, SQL schema, and workflow definition are documented.

### T-002 Reviewer Queue and Decision Workflow

- Status: done
- Outcome: reviewers can inspect a packet, evidence, findings, and submit a final decision.

### T-003 Real PDF Intake

- Status: done
- Outcome: PDFs upload locally, are validated, stored, served through a protected API route, and shown in the review workspace.

### T-004 Text-PDF Extraction and Deterministic Rules

- Status: done
- Outcome: text PDFs provide vendor name, tax ID, payment terms, and coverage candidates; missing documents, name mismatches, and tax gaps create findings.

### T-005 Scan-Safe OCR Workflow

- Status: done
- Outcome: scanned PDFs enter `OCR required` rather than receiving fabricated fields; Azure Document Intelligence is an optional adapter.

### T-006 Regression Evaluation Harness

- Status: done
- Outcome: an isolated `make evaluate` suite verifies missing insurance, name mismatch, tax gap, scan/OCR fallback, approval guard, and correction audit.

### T-007 Reviewer Field Corrections

- Status: done
- Outcome: reviewers can correct an extracted field without overwriting the model output; original value, correction, reason, reviewer, and time are retained.

### T-008 Approval Override Guard

- Status: done
- Outcome: approving a packet with open high-risk findings requires an explicit override reason in both UI and API.

### T-009 Finding Lifecycle and Resolution Notes

- Status: done
- Outcome: reviewers can mark findings `resolved`, `accepted risk`, or `not applicable` with an append-only explanation; approval protection considers only open high-risk findings.

### T-010 Queue Operations Metrics

- Status: done
- Outcome: the queue reports open high-risk packets, OCR-blocked packets, missing documents, average review age, and decision override rate from live queue data.

### T-012 Background Processing Boundary

- Status: done
- Outcome: new packets create queued processing runs; a polling worker claims pending packets and Docker Compose includes a worker service. The evaluation suite verifies worker handoff.

### T-013 Access Control and Audit Hardening

- Status: done
- Outcome: trusted actor identity and role checks protect operational routes; reviewer names are server-controlled; privileged actions emit append-only hash-chained audit events and admins can export the ledger.

### T-011 Actual Azure OCR Validation

- Status: done
- Outcome: a real scanned W-9 was processed through Azure Document Intelligence; page-level OCR text, extracted legal name and tax ID, and evidence were verified in the reviewer workflow.

## Now

### T-014 Production Storage and Deployment

- Status: done
- Outcome: production-ready storage, database, secret, health-check, and deployment contracts replace reliance on local files and SQLite. Cloud resource provisioning remains a separate, account-dependent release prerequisite.

### T-015 Policy Configuration and Evaluation Dashboard

- Status: done
- Outcome: policy catalogue, versioned rule-revision workflow, regression-score recording, guarded activation, evaluation metrics, and audit events are available through admin-only APIs. A rule revision cannot activate unless all recorded regression scores meet the 0.95 threshold.

## Next

## Later

## Operating Rule

Work only one `Now` ticket at a time. A ticket moves to `Done` only after its
acceptance criteria and the relevant regression checks pass.
