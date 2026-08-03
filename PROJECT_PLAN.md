# Vendor Onboarding Document Intelligence

## 1. What the project is

Vendor Onboarding Document Intelligence is a bounded enterprise document workflow system for reviewing vendor onboarding packets.

It is not a generic chatbot, not a contract summarizer, and not a multi-agent demo for its own sake.

The system should help a procurement or finance reviewer answer a practical operational question:

"Can this vendor packet move forward, what is missing or inconsistent, and what evidence supports that decision?"

## 2. Practical problem to solve

In real vendor onboarding, a reviewer often has to inspect multiple documents, extract key fields, compare values across files, check policy thresholds, and decide whether to approve, send back for revision, or escalate.

This process is slow because:

- documents are scanned PDFs or inconsistent templates
- key values appear across several files
- reviewers manually cross-check names, tax IDs, payment terms, and insurance coverage
- policies are applied inconsistently
- decisions are hard to audit later

The practical problem is not "how do we chat with documents?"

The practical problem is:

- reduce manual review time
- catch missing or conflicting information
- apply business rules consistently
- give reviewers evidence-backed recommendations
- preserve human control for high-impact decisions

### 2.1 Real business context

This workflow sits inside a broader procure-to-pay process.

A company cannot simply start paying a new vendor immediately. Before payment is enabled in ERP systems such as SAP or Oracle, the vendor must be onboarded into internal systems and reviewed for completeness, correctness, and policy compliance.

Typical packet contents can include:

- W-9
- insurance certificate
- contract
- vendor registration form
- bank account form
- NDA

The project focuses on one narrow but painful step in that larger lifecycle:

- vendor submits documents
- reviewer checks the packet
- reviewer decides whether the packet can move forward
- approved vendor can be created and paid later in downstream systems

That framing matters because this is fundamentally an operations approval problem, not just a document extraction problem.

## 3. Project direction recovered from earlier discussions

The earlier project discussions converged on a few important decisions:

### 3.1 Focus on one real workflow, not four parallel AI demos

Earlier thinking started from a broad "enterprise AI systems" idea spanning retrieval, workflow, code agents, and evaluation. That direction was later narrowed into a more mature approach:

- choose one high-value workflow
- build a complete decision loop around it
- use evaluation throughout
- avoid pretending to build a full platform or operating system

### 3.2 Prefer bounded workflow intelligence over generic agent complexity

The project should feel like a real business system:

- deterministic checks first
- LLMs used only where ambiguity exists
- explicit workflow state
- reviewer approval for risky outcomes
- auditability and evidence trails

This means we should avoid:

- complex multi-agent conversations without clear need
- platform claims that imply too much scope
- too many connectors in v1
- broad autonomous actions

### 3.3 Evaluation is part of the product, not a final add-on

The prior design work emphasized that the difference between a polished demo and an engineering-quality project is evaluation.

For this project, evaluation should be present from the start:

- extraction quality
- mismatch detection quality
- policy rule accuracy
- routing recommendation quality
- reviewer agreement
- failure slice analysis

## 4. Product definition

### 4.1 One-line definition

A document workflow system that extracts, validates, and reviews vendor onboarding packets across multiple business documents.

### 4.2 Primary users

- procurement operations analysts
- finance operations reviewers
- vendor risk reviewers
- security or compliance reviewers

### 4.3 MVP scenario

Support one onboarding packet containing:

- vendor contract
- W-9
- insurance certificate

Optional realism upgrade after MVP:

- vendor registration form
- bank account form

### 4.4 Core user story

A reviewer uploads or opens a vendor packet and wants to know:

- which required documents are missing
- what key fields were extracted
- whether values conflict across documents
- whether policy thresholds are violated
- whether the packet should be approved, reviewed manually, or escalated

### 4.5 Why this project is worth doing

This project should not be justified as "workflow automation" alone, because mature workflow tools already exist.

The real differentiator is document decision intelligence:

- multiple documents may disagree
- extracted values may be noisy
- some fields require normalization before comparison
- some cases can be decided deterministically
- some cases require bounded semantic interpretation
- some cases should explicitly defer to a human

That is the engineering and AI value of the system.

## 5. Desired system behavior

### 5.1 Inputs

- PDF document bundle
- OCR text and page structure
- extraction schema
- policy rules from procurement and finance
- historical reviewer decisions

### 5.2 Outputs

- extracted vendor profile
- completeness status
- cross-document mismatch findings
- policy violations
- approve / needs review / escalate recommendation
- evidence snippets and audit trail

Suggested fuller decision taxonomy after MVP:

- approve
- needs review
- request resubmission
- escalate to finance
- escalate to compliance
- reject

### 5.3 MVP user flow

1. Reviewer opens the package queue.
2. Reviewer selects one vendor packet.
3. System shows expected and uploaded documents.
4. OCR and parsing run on each file.
5. Extraction service captures core fields.
6. Validation service checks confidence and normalization.
7. Cross-document comparison detects mismatches.
8. Policy engine applies rules.
9. Semantic review handles ambiguous cases.
10. System recommends approve, needs review, or escalate.
11. Human reviewer confirms, overrides, and leaves notes.
12. Final decision and evidence are stored.

## 6. Architecture we should build

The architecture should be simple, explainable, and grounded in the workflow.

### 6.1 Ingestion layer

Responsibilities:

- accept document bundles
- register package metadata
- store source files
- trigger OCR and parsing

### 6.2 OCR and parsing layer

Responsibilities:

- extract text from scanned or digital PDFs
- preserve page references
- preserve document boundaries
- create normalized text blocks for extraction

### 6.3 Extraction layer

Responsibilities:

- extract a fixed schema of business fields
- attach confidence scores
- map each field to source page or snippet

Suggested MVP fields:

- vendor legal name
- tax ID
- payment terms
- insurance coverage amount
- certificate expiration date
- contract effective date
- contract end date
- insurance provider

### 6.4 Validation layer

Responsibilities:

- normalize extracted values
- compare equivalent fields across documents
- detect missing required fields
- detect low-confidence extractions

This layer is more important than plain OCR because enterprise reviewers do not make decisions on raw extracted strings alone.

It should handle examples such as:

- punctuation or casing differences in legal names
- company suffix variations such as `LLC`, `Inc.`, or `Corporation`
- date normalization across formats
- money normalization across textual and numeric expressions
- strict vs fuzzy matching depending on field risk

### 6.5 Policy engine

Responsibilities:

- apply deterministic business rules
- assign severity
- explain which rule was triggered

Suggested MVP rules:

- insurance coverage below threshold
- payment terms exceed allowed maximum
- tax ID missing
- vendor legal name mismatch
- expired insurance certificate
- certificate expiration too close to onboarding date

### 6.6 Semantic reviewer

Responsibilities:

- resolve cases rules cannot confidently decide
- inspect evidence snippets
- classify ambiguity or escalation reason

This should be narrow and bounded. It is not an open-ended chat agent.

Good use cases for this layer:

- interpreting ambiguous payment-term language
- deciding whether two near-matching legal names likely refer to the same entity
- explaining why the system is abstaining or requesting human review

### 6.7 Decision and audit layer

Responsibilities:

- generate recommendation
- support human override
- store reviewer notes
- preserve evidence used in the decision

The system should be comfortable saying "insufficient evidence" rather than forcing a false clean decision.

## 7. Recommended technical boundaries

These boundaries are important because earlier discussions repeatedly warned against overbuilding.

### 7.1 In scope for MVP

- one workflow only: vendor onboarding packet review
- three document types only
- 8 to 10 extracted fields
- 5 to 7 deterministic policy rules
- human-in-the-loop final decision
- reviewer-facing UI or demo surface
- evaluation dataset and benchmark

### 7.2 Out of scope for MVP

- full contract clause reasoning
- automatic contract redlining
- broad procurement system integrations
- autonomous approvals without human confirmation
- many vendor packet formats
- full enterprise permissions platform
- complex multi-agent orchestration

### 7.3 Positioning constraints

We should describe the project as:

- a reliable enterprise workflow AI system
- a multi-document review and validation system
- an evaluation-driven document intelligence workflow

For broader portfolio storytelling, we can also describe the underlying pattern as:

- enterprise document decision intelligence

In that framing, vendor onboarding is the first workflow, not necessarily the last one.

Possible future workflow variants:

- customer KYC
- loan document review
- insurance claim intake
- employee onboarding
- supplier compliance review

We should not describe it as:

- an enterprise AI operating system
- a general-purpose vendor management platform
- a legal AI platform

## 8. Data model direction

Recovered from earlier design work, the current MVP schema draft is:

- `vendors`
- `document_packages`
- `documents`
- `extracted_fields`
- `policy_rules`
- `validation_findings`
- `review_decisions`

This is the right backbone for the first version.

### 8.1 Recommended schema additions

To make the project more engineering-mature, add:

- `document_requirements`
- `field_normalizations`
- `field_comparisons`
- `evaluation_cases`
- `evaluation_runs`
- `decision_evidence`
- `routing_policies`
- `processing_runs`

These additions help separate:

- required vs uploaded docs
- raw extraction vs normalized values
- package findings vs field-level comparisons
- product behavior vs benchmark behavior

They also make it possible to represent the real system logic more faithfully:

- one package contains many documents
- one document can contain many extracted fields
- one field can appear in multiple documents
- normalized fields feed comparison logic
- comparisons create findings
- findings and policy rules create routing decisions
- reviewer overrides must remain auditable and reproducible

## 9. Evaluation plan

This should become one of the strongest parts of the project.

### 9.1 Core metrics

- extraction accuracy
- field-level precision and recall
- mismatch detection precision and recall
- policy rule accuracy
- routing accuracy
- abstain or uncertainty quality
- reviewer agreement rate
- median review time reduction

### 9.2 Evaluation dataset

Build a labeled dataset of vendor packets with:

- expected extracted fields
- expected mismatch findings
- expected policy findings
- expected final routing decision

Suggested initial scale:

- 30 to 50 cases for first benchmark
- 100 to 150 cases for stronger project credibility

### 9.3 Benchmark slices

Track performance by slice:

- clean digital PDFs
- scanned low-quality PDFs
- missing document cases
- conflicting-name cases
- low insurance coverage cases
- ambiguous payment-term language

## 10. What maturity looks like

To reach the level of stronger portfolio projects, the project should demonstrate:

- a specific operational problem
- clear scope boundaries
- realistic data model
- evidence-grounded outputs
- measurable evaluation
- human review for risky decisions
- architecture that matches the workflow

The maturity should come from:

- solving a real business task well
- showing failure handling
- measuring system quality
- presenting thoughtful product boundaries

Not from:

- claiming too many AI buzzwords
- adding many agents or connectors without proof of need
- inflating the project into a fake enterprise platform

### 10.1 UI maturity

One strong improvement suggested by the analysis is to make the reviewer interface feel like real document-review software rather than a student dashboard.

The UI should likely center on a three-panel review experience:

- left: packet and document list
- center: document viewer with page-level context
- right: extracted fields, issues, and decisions

Key elements:

- finding severity
- source page references
- evidence snippets
- missing document indicators
- clear reviewer actions

This is worth prioritizing because it reinforces the idea that the system assists a reviewer rather than merely displaying model output.

## 11. Recommended next-phase structure

### Phase 1. Finalize product contract

Deliverables:

- crisp problem statement
- target users
- required document list
- extracted field list
- policy rule list
- approve / review / escalate definitions

Exit criteria:

- one-page product definition is stable

### Phase 2. Finalize data and schema

Deliverables:

- SQL schema v1
- seed package design
- labeled field dictionary
- finding taxonomy

Exit criteria:

- database can represent all MVP decisions cleanly

### Phase 3. Build the evaluation set first

Deliverables:

- 30 to 50 labeled onboarding cases
- expected extraction outputs
- expected findings
- expected routing decisions

Exit criteria:

- we can measure baseline quality before adding more intelligence

### Phase 4. Build deterministic baseline pipeline

Deliverables:

- OCR/parsing pipeline
- schema-based extraction baseline
- normalization rules
- field comparison engine
- rule engine

Exit criteria:

- baseline system can process a packet end to end without LLM-heavy logic

### Phase 5. Add bounded LLM assistance

Deliverables:

- semantic resolution for ambiguous fields
- evidence-backed explanations
- reviewer-facing summaries

Exit criteria:

- LLM adds value only where deterministic logic is weak

### Phase 6. Build reviewer workflow surface

Deliverables:

- package queue
- package detail view
- findings panel
- evidence panel
- decision submission flow

Exit criteria:

- end-to-end demo is understandable in under 5 minutes

### Phase 7. Add evaluation and observability

Deliverables:

- benchmark runner
- versioned evaluation reports
- slice analysis
- latency and failure logging

Exit criteria:

- you can explain where the system works and where it fails

### Phase 8. Polish for portfolio readiness

Deliverables:

- architecture diagram
- README
- demo script
- screenshots
- case-study narrative

Exit criteria:

- project can be defended in interviews as an engineering system, not just a demo

## 12. Immediate next tasks

The most useful next concrete tasks are:

1. lock the exact MVP document set and field list
2. upgrade the SQL draft into schema v1 with comparison and evaluation tables
3. define 10 to 15 policy rules, then cut to the best 5 to 7 for MVP
4. design 20 seed vendor packets with ground truth
5. decide the first extraction method baseline
6. write the final README and product spec from this plan
7. sketch the reviewer UI around document list + PDF view + findings panel
8. prepare a short README-first explanation of where vendor onboarding sits inside the procure-to-pay lifecycle

## 13. Working thesis

If we execute this well, the project will show that you can:

- define a real enterprise operations problem
- structure a document intelligence workflow around business decisions
- combine OCR, extraction, validation, rules, and bounded LLM reasoning
- keep a human in control for consequential decisions
- evaluate the system like an engineer instead of stopping at a demo

That is the strongest version of the direction recovered from the earlier discussions.

## 14. Important distinction

This project is not trying to replace SAP Ariba, Coupa, Oracle Procurement, or a full vendor management platform.

The correct conceptual scope is:

- existing procurement or operations system
- vendor uploads documents
- this project acts as an intelligent review layer
- structured findings and recommendations are produced
- human reviewer confirms the outcome

That keeps the scope realistic while preserving the part of the problem that is actually interesting from an AI and systems perspective.
