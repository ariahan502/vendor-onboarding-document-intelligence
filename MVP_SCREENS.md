# MVP Screens

## Goal

Define the minimum set of product screens for `Vendor Onboarding Document Intelligence`.

These screens should support the full reviewer workflow from packet intake to final decision, while keeping the MVP focused and realistic.

## 1. Design principle

The UI should feel like:

- a document review workspace
- an internal operations tool
- a reviewer decision system

It should not feel like:

- a chatbot
- a generic dashboard with no workflow
- a document upload demo

## 2. MVP screen list

The MVP should have these core screens:

1. `Package Queue`
2. `Packet Review Workspace`
3. `Findings and Evidence`
4. `Decision and Review History`
5. `Evaluation / Admin Summary`

In implementation, some of these can be combined, but they should still exist as clear product surfaces.

## 3. Package Queue

### Purpose

Give reviewers a worklist of submitted vendor packets and help them quickly identify which cases need attention.

### Main user

- procurement reviewer
- finance ops reviewer

### Key questions this screen answers

- which packets are waiting?
- which packets are blocked by missing documents?
- which packets have severe findings?
- which packets can likely move quickly?

### Main content

- package ID
- vendor name
- submission date
- packet status
- required document completeness
- current recommendation
- finding count
- highest severity
- assigned reviewer

### Suggested statuses

- `uploaded`
- `processing`
- `ready_for_review`
- `needs_vendor_resubmission`
- `escalated`
- `approved`
- `rejected`

### Primary actions

- open packet
- filter by status
- filter by severity
- filter by missing documents
- sort by submission date or priority

### UI notes

This should look like a serious review queue, not a marketing dashboard.

Good visual cues:

- severity badges
- missing document indicators
- recommendation chips
- row-level quick status scanning

## 4. Packet Review Workspace

### Purpose

This is the core screen of the product.

It should let a reviewer inspect the packet, verify extracted data, understand findings, and make a decision without context-switching.

### Layout

Use a three-panel layout:

- left: packet and document navigation
- center: PDF viewer
- right: extracted fields, findings, and decision actions

### Left panel

Show:

- packet summary
- list of uploaded documents
- expected but missing documents
- document type labels
- processing status per document

Example document list:

- `Contract.pdf`
- `W-9.pdf`
- `Insurance_Certificate.pdf`
- `Vendor_Form.pdf` if added later

### Center panel

Show:

- selected PDF document
- page navigation
- zoom controls
- highlighted evidence regions if available
- anchor jumps from fields or findings

The center panel should help the reviewer trust the system by making source verification easy.

### Right panel

Show:

- extracted field summary
- confidence warnings
- cross-document mismatches
- policy violations
- recommended decision
- reviewer actions

### Reviewer actions

- approve
- mark needs review
- request resubmission
- escalate
- reject
- add note

For MVP, you may choose a smaller final action set in logic, but the UI should be designed with realistic operational actions in mind.

## 5. Extracted Fields section

### Purpose

Show the structured profile inferred from the packet.

### Required fields for MVP

- vendor legal name
- tax ID
- payment terms
- insurance coverage
- insurance expiration date
- contract effective date
- contract end date
- insurance provider

### For each field, show

- field label
- extracted value
- normalized value if different
- source document
- source page
- confidence score or confidence band

### Important interaction

Clicking a field should jump the PDF viewer to the relevant source page.

## 6. Findings section

### Purpose

Help the reviewer understand what is wrong, risky, incomplete, or ambiguous in the packet.

### Finding types

- missing required document
- missing required field
- cross-document mismatch
- low-confidence extraction
- policy violation
- ambiguity requiring human review

### For each finding, show

- title
- severity
- short explanation
- impacted document(s)
- impacted field(s)
- evidence link
- suggested next action

### Example findings

- `Vendor legal name mismatch across contract and W-9`
- `Insurance coverage below minimum threshold`
- `Tax ID missing from vendor packet`
- `Payment terms may exceed policy limit`

## 7. Evidence section

### Purpose

This is where the product earns trust.

The reviewer should never have to rely on a naked system claim if evidence can be shown.

### Show

- source document name
- page number
- quoted snippet
- highlighted field region if available
- related finding or field

### Example evidence card

- `Contract.pdf`
- `Page 3`
- snippet showing `ABC Consulting Group LLC`
- linked finding: `Legal name mismatch`

### UX rule

Every serious finding should have visible evidence or clearly state why evidence is missing.

## 8. Decision panel

### Purpose

Let the reviewer see the system recommendation and commit the final outcome.

### Show

- recommended decision
- summary reason
- major blocking findings
- uncertainty or abstain message if applicable
- reviewer note input
- final action buttons

### Recommendation types for MVP

- `approve`
- `needs_review`
- `escalate`

### Recommended future expansion

- `request_resubmission`
- `escalate_to_finance`
- `escalate_to_compliance`
- `reject`

### Important behavior

The system recommendation should never be visually indistinguishable from the human final decision.

The UI must make clear:

- what the system recommends
- what the reviewer decided

## 9. Decision and Review History

### Purpose

Preserve auditability and support trust in the workflow.

### Show

- prior review decisions
- reviewer name
- timestamp
- reviewer notes
- system recommendation at the time
- major findings at the time

### Why it matters

This makes the product feel like enterprise software instead of a one-time demo.

## 10. Evaluation / Admin Summary

### Purpose

This is not the primary reviewer screen, but it is important for product maturity and demo credibility.

### Main audience

- project owner
- engineer
- evaluator

### Show

- extraction accuracy
- finding precision / recall
- routing accuracy
- reviewer agreement
- benchmark runs by version

### Why it belongs in MVP planning

Even if the first UI version is simple, this screen reinforces that the system is measured, not just shown.

## 11. Minimum end-to-end user flow

1. Reviewer opens `Package Queue`.
2. Reviewer selects a packet marked `ready_for_review`.
3. Reviewer lands in `Packet Review Workspace`.
4. Reviewer inspects extracted fields.
5. Reviewer checks findings and evidence.
6. Reviewer reviews the system recommendation.
7. Reviewer approves, escalates, or flags for review.
8. Decision is stored in `Decision and Review History`.

## 12. What can be deferred

These do not need to be in the first UI cut:

- multi-reviewer collaboration
- comments thread
- vendor-facing portal
- bulk actions
- advanced analytics dashboards
- granular role-based permissions
- complex SLA tracking

## 13. UI quality bar

The MVP should aim for:

- clean information density
- obvious workflow progression
- strong visual distinction between fields, findings, evidence, and decisions
- low-friction source verification

It should avoid:

- chat-first interaction
- empty whitespace-heavy marketing layout
- decorative widgets that do not help review work
- burying evidence behind too many clicks

## 14. Recommendation

If we need to simplify implementation, the best compromise is:

- build `Package Queue`
- build one strong `Packet Review Workspace`
- include findings, evidence, and decision panel inside that workspace
- add a lightweight `Evaluation / Admin Summary` later

That gives us the highest-value reviewer workflow without spreading effort too thin.

## 15. Next step

Now that the screens are defined, the next most useful artifact is:

- `SCHEMA_V1.md` or `schema.sql`

because the UI and the workflow should now drive the backend data model.
