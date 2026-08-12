# Schema V1

## Goal

Explain the purpose of the first database schema for `Vendor Onboarding Document Intelligence`.

This document answers:

- why each table exists
- how tables map to the reviewer workflow
- how tables support the UI
- how tables support evaluation and reproducibility

The SQL definition lives in [schema.sql](/Users/hanlingjuan/Documents/vendor-onboarding-project/schema.sql).

## 1. Design principles

The schema is designed around a reviewer decision workflow, not around a generic chatbot or a simple OCR pipeline.

It is built to support:

- one vendor packet containing multiple documents
- extraction from each document
- normalization of extracted values
- comparison across documents
- findings and policy decisions
- evidence-backed reviewer decisions
- reproducible evaluation runs

## 2. Core workflow mapping

The schema supports this flow:

1. a vendor exists
2. a vendor submits one onboarding packet
3. the packet contains multiple documents
4. each document is processed
5. fields are extracted from documents
6. extracted values are normalized
7. equivalent fields are compared across documents
8. findings are generated
9. policy and routing logic produce a recommendation
10. evidence is shown to a reviewer
11. a reviewer makes the final decision
12. the system is evaluated against labeled cases

## 3. Entity overview

There are six main groups of tables:

1. business entities
2. document processing
3. normalization and comparison
4. findings and decision support
5. human review
6. evaluation

## 4. Business entities

### `vendors`

Purpose:

- represents the vendor organization under review

Why it exists:

- multiple packets can conceptually belong to the same vendor over time
- vendor identity should not be embedded only inside documents

Key fields:

- `vendor_id`
- `legal_name`
- `normalized_legal_name`
- `tax_id`
- `country`
- `category`

UI mapping:

- package queue vendor label
- packet header summary

### `document_packages`

Purpose:

- represents one reviewable onboarding packet

Why it exists:

- the reviewer is not reviewing isolated files
- the reviewer is reviewing a packet-level decision object

Key fields:

- `package_id`
- `vendor_id`
- `package_status`
- `submitted_at`
- `assigned_reviewer`
- `system_recommendation`
- `final_decision`

UI mapping:

- package queue rows
- packet review workspace header
- review status filtering

This is one of the most important tables in the schema.

### `document_requirements`

Purpose:

- tracks which document types are required and whether the packet satisfies them

Why it exists:

- missing documents are part of the decision workflow
- this should be explicit data, not implicit UI logic

Example use:

- W-9 required but missing
- insurance certificate required but uploaded

UI mapping:

- missing document indicators in queue
- missing document alerts in packet review workspace

## 5. Document processing

### `documents`

Purpose:

- stores metadata for each uploaded document in a packet

Why it exists:

- one packet contains many files
- each file needs its own type, status, and processing lifecycle

Key fields:

- `document_id`
- `package_id`
- `doc_type`
- `file_name`
- `page_count`
- `upload_status`
- `ocr_status`
- `parse_status`

UI mapping:

- left panel document list
- document processing state
- selected PDF context

### `processing_runs`

Purpose:

- records each OCR, extraction, parsing, or model processing attempt

Why it exists:

- document processing is asynchronous
- failures, retries, model versions, and prompt versions should be traceable

Key fields:

- `processing_run_id`
- `run_type`
- `run_status`
- `model_name`
- `model_version`
- `prompt_version`
- `started_at`
- `completed_at`
- `error_message`

Engineering value:

- auditability
- retry visibility
- debugging
- reproducibility

## 6. Extraction and normalization

### `extracted_fields`

Purpose:

- stores raw extracted fields from each document

Why it exists:

- extraction results need to remain separate from normalized values
- multiple fields can be extracted from one document
- each extracted field needs source traceability

Key fields:

- `field_id`
- `document_id`
- `field_name`
- `raw_value`
- `value_type`
- `confidence`
- `source_page`
- `source_span_text`
- `source_bbox`

UI mapping:

- extracted fields panel
- field-level source jumps into PDF

### `field_normalizations`

Purpose:

- stores normalized versions of extracted fields

Why it exists:

- reviewers do not decide from raw OCR strings alone
- cross-document comparison requires normalized representations

Examples:

- `ABC CONSULTING, L.L.C.` -> `abc consulting`
- `$1 million` -> `1000000`
- `08/01/2026` -> `2026-08-01`

Key fields:

- `normalization_id`
- `field_id`
- `normalized_value`
- `normalized_value_json`
- `normalization_method`
- `normalization_confidence`

Why this table matters:

- it makes the system more than an OCR pipeline
- it captures one of the real business logic layers in the product

## 7. Cross-document validation

### `field_comparisons`

Purpose:

- stores explicit comparisons between fields that should be checked against each other

Why it exists:

- packet review depends on comparing related fields across documents
- comparison results should not be buried inside ad hoc application code

Examples:

- W-9 legal name vs contract legal name
- insurance coverage vs policy threshold
- tax ID across vendor form and W-9

Key fields:

- `comparison_id`
- `package_id`
- `left_field_id`
- `right_field_id`
- `comparison_type`
- `comparison_status`
- `similarity_score`
- `requires_review`
- `explanation`

UI mapping:

- mismatch findings
- comparison evidence drill-down

This is another table that makes the schema meaningfully stronger than a generic document-processing app.

## 8. Policy and decision support

### `policy_rules`

Purpose:

- stores deterministic policy rules

Why it exists:

- policy checks should be explicit and versioned
- rules are part of the business contract of the system

Examples:

- insurance coverage must be at least threshold
- insurance expiration must exceed minimum window
- tax ID must be present
- standard payment terms may not exceed allowed maximum

Key fields:

- `rule_id`
- `rule_code`
- `rule_description`
- `severity`
- `decision_impact`
- `condition_expression`
- `rule_version`

### `routing_policies`

Purpose:

- defines how findings and rule results map to recommendation states

Why it exists:

- recommendation logic should be explicit, not hand-waved inside UI code

Examples:

- no severe findings -> approve
- missing required doc -> needs review or resubmission
- severe compliance issue -> escalate

This table becomes more valuable as the workflow becomes more realistic.

### `validation_findings`

Purpose:

- stores the concrete issues detected in a packet

Why it exists:

- reviewer decisions are driven by findings, not just extracted values
- findings are the language the UI and workflow both use

Types include:

- missing document
- missing field
- mismatch
- low-confidence extraction
- policy violation
- ambiguity requiring review

Key fields:

- `finding_id`
- `package_id`
- `document_id`
- `comparison_id`
- `rule_id`
- `finding_type`
- `severity`
- `finding_status`
- `title`
- `description`
- `suggested_action`
- `requires_human_review`

UI mapping:

- findings list
- severity summaries
- recommendation explanations

## 9. Evidence and human review

### `decision_evidence`

Purpose:

- stores the evidence snippets shown to the reviewer

Why it exists:

- the system should not make unsupported claims
- evidence should be a first-class object, not just generated text

Key fields:

- `evidence_id`
- `package_id`
- `finding_id`
- `field_id`
- `document_id`
- `evidence_type`
- `page_num`
- `snippet_text`
- `bbox`

UI mapping:

- evidence cards
- PDF highlights
- click-through source verification

### `review_decisions`

Purpose:

- stores the human review outcome

Why it exists:

- the final decision belongs to the reviewer
- the system recommendation and reviewer override should both be preserved

Key fields:

- `decision_id`
- `package_id`
- `reviewer`
- `system_recommendation`
- `final_decision`
- `override_reason`
- `reviewer_comment`
- `decision_at`

UI mapping:

- decision panel
- review history
- audit trail

## 10. Evaluation

### `evaluation_cases`

Purpose:

- stores labeled benchmark cases

Why it exists:

- evaluation should be a first-class system capability
- we need expected fields, findings, and decisions for known cases

Key fields:

- `eval_case_id`
- `package_id`
- `case_name`
- `case_slice`
- `expected_fields`
- `expected_findings`
- `expected_decision`

Examples of slices:

- clean digital PDF
- low-quality OCR
- missing W-9
- legal name mismatch
- ambiguous payment terms

### `evaluation_runs`

Purpose:

- stores the results of benchmark runs over evaluation cases

Why it exists:

- versioned testing matters
- model changes, prompt changes, and rule changes should be comparable

Key fields:

- `eval_run_id`
- `eval_case_id`
- `run_label`
- `model_name`
- `model_version`
- `prompt_version`
- `rule_version`
- `extraction_score`
- `finding_score`
- `routing_score`
- `reviewer_agreement_score`

Product value:

- supports regression testing
- supports performance comparison
- helps explain where the system improves or fails

## 11. Why this schema is stronger than a simple MVP schema

The early simple schema was useful:

- vendors
- packages
- documents
- extracted fields
- findings
- decisions

But this V1 schema is stronger because it adds the real layers the system depends on:

- explicit document requirements
- processing runs
- normalization
- comparison
- evidence
- rule versioning
- evaluation runs

These additions make the system a real engineered workflow system rather than a one-shot extraction flow.

## 12. How this maps to the UI

### Package Queue

Main tables:

- `document_packages`
- `document_requirements`
- `validation_findings`

### Packet Review Workspace

Main tables:

- `documents`
- `extracted_fields`
- `field_normalizations`
- `field_comparisons`
- `validation_findings`
- `decision_evidence`

### Decision and Review History

Main tables:

- `review_decisions`
- `document_packages`

### Evaluation / Admin Summary

Main tables:

- `evaluation_cases`
- `evaluation_runs`
- optionally `processing_runs`

## 13. What can change later

This schema is intentionally a strong V1, not a final forever model.

Possible future changes:

- separate users and reviewer identities into their own tables
- add packet comments or collaboration threads
- add vendor-facing resubmission cycles
- add workflow assignments and SLAs
- add more formal versioned document templates
- add more granular evidence linkage

## 14. Recommendation

This schema is the right level for the current project stage:

- detailed enough to support real workflow design
- explicit enough to support evaluation and reproducibility
- still small enough to implement in an MVP repository

## 15. Next step

The next best step is to move from planning into implementation structure:

- create repo folders
- define backend models from `schema.sql`
- create seed data for sample packets
- define the first API surface for package queue and packet review
