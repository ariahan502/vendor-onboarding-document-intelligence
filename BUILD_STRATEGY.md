# Build Strategy

## Goal

Build `Vendor Onboarding Document Intelligence` efficiently without wasting time rebuilding commodity infrastructure or getting trapped inside someone else's product architecture.

The right strategy is:

- reuse generic infrastructure
- design our own business logic
- keep the project scoped around the reviewer decision workflow

## 1. Core principle

We are not trying to build:

- a full procurement platform
- a full vendor management system
- a generic chat-with-PDF app
- a hackathon-style multi-agent prototype

We are trying to build:

- an intelligent document review layer for vendor onboarding packets

That means we should borrow the parts that are generic and low-differentiation, and own the parts that define the product's value.

## 2. What to reuse

These are good candidates for reuse from open-source starters, components, or small subsystems.

### 2.1 App shell and infrastructure

- FastAPI or backend project scaffold
- Next.js or React admin/dashboard scaffold
- file upload flow
- auth boilerplate if needed later
- background jobs or task queue setup
- Docker setup
- database migrations setup
- logging and config management

### 2.2 Document handling foundation

- PDF rendering/viewer component
- OCR integration wrapper
- document text extraction pipeline
- page-level coordinate or snippet mapping utilities
- table extraction or form parsing helpers

### 2.3 Reviewer UI building blocks

- left-nav document list
- center-panel PDF viewer
- right-panel issue or field cards
- data table components
- badges, severity labels, filters, and action bars

### 2.4 Evaluation and ops utilities

- experiment tracking skeleton
- benchmark runner skeleton
- trace/log viewer utilities
- chart components for metrics dashboards

## 3. What we must build ourselves

These are the parts that actually make this project yours.

### 3.1 Business data model

We should own:

- `vendors`
- `document_packages`
- `documents`
- `document_requirements`
- `extracted_fields`
- `field_normalizations`
- `field_comparisons`
- `validation_findings`
- `policy_rules`
- `decision_evidence`
- `review_decisions`
- `evaluation_cases`
- `evaluation_runs`

### 3.2 Domain logic

We should own:

- document completeness checks
- extracted field schema
- normalization rules for names, dates, money, and IDs
- cross-document comparison logic
- finding taxonomy
- severity logic
- routing decision logic
- abstain / needs-review behavior
- human override flow

### 3.3 AI-specific logic

We should own:

- where LLMs are allowed to participate
- where rules must dominate
- evidence-grounded explanation design
- ambiguity handling thresholds
- confidence thresholds
- evaluation datasets and scoring

### 3.4 Product behavior

We should own:

- what the reviewer sees first
- how findings are grouped
- how evidence is displayed
- what actions are available
- what states a packet can move through

## 4. What not to use as the primary base

These may be useful for ideas, but they are usually poor foundations for this project.

### 4.1 Full procurement or ERP platforms

Avoid using these as the implementation base:

- supplier lifecycle suites
- procurement portals
- ERP procurement products

Why:

- too much unrelated product scope
- wrong assumptions about permissions, integrations, and workflows
- hard to modify locally
- you will spend more time fighting the platform than building your intelligence layer

### 4.2 Generic chat-with-PDF repos

Avoid these as the main base.

Why:

- wrong product interaction model
- weak support for structured findings and routing
- often centered on open-ended QA instead of reviewer workflow

### 4.3 Hackathon agent repos

Avoid these as the main base.

Why:

- often shallow architecture
- unclear reliability boundaries
- weak data modeling
- usually over-claim on product scope

### 4.4 Full contract intelligence products

Use for inspiration only unless the codebase is unusually modular.

Why:

- contract analysis is not the same as packet-level review
- often too clause-centric
- may not support cross-document validation well

## 5. What kind of base is best

The best primary base is usually one of these:

### Option A. Full-stack app starter

Use when we want maximum control.

Good for:

- backend + frontend scaffold
- database + jobs + API structure
- adding our own document workflow from scratch

Tradeoff:

- more work than borrowing an existing document app
- but much cleaner ownership of product logic

### Option B. Document review / IDP UI starter

Use when we want to accelerate the reviewer experience.

Good for:

- document viewer
- extraction panel
- human review layout

Tradeoff:

- we still need to rebuild the vendor onboarding logic
- must be careful not to inherit the wrong data model

### Option C. Backend starter plus separate UI components

Use when no single base fits well.

Good for:

- flexible architecture
- controlled complexity
- easier long-term maintainability

Tradeoff:

- more assembly work

## 6. Decision rule for selecting a base

A candidate base is good if it saves time on infrastructure without imposing the wrong business model.

Use this checklist.

### 6.1 Strong candidate

A repo is a strong candidate if:

- it has clean code structure
- it supports document upload and storage
- it has a usable document viewer or admin shell
- it is easy to run locally
- its data model is lightweight or replaceable
- it does not force a chat-centric UX

### 6.2 Weak candidate

A repo is a weak candidate if:

- its architecture is confusing
- it has too many domain assumptions
- it is built around generic chat
- it is tied to unrelated workflows
- it lacks clear data boundaries
- it looks impressive but has little engineering depth

## 7. Recommended build split

This is the split I recommend for this project.

### Reuse

- app scaffold
- PDF viewer
- file upload
- OCR plumbing
- base dashboard components
- task runner / background worker skeleton
- charts and tables

### Build

- package schema
- extraction schema
- normalization engine
- comparison engine
- finding generation
- policy engine
- routing engine
- evidence model
- review workflow
- evaluation harness

## 8. Practical execution order

### Phase 1. Lock the architecture contract

Before choosing a base, finalize:

- MVP documents
- field list
- decision states
- findings taxonomy
- must-have screens

### Phase 2. Shortlist base types, not repos first

Choose among:

- full-stack starter
- document review starter
- backend starter + custom UI

Do not start by randomly cloning flashy repos.

### Phase 3. Evaluate 3 to 5 candidate bases

For each candidate, score:

- ease of local setup
- UI usefulness
- backend cleanliness
- document support
- ability to replace schema
- risk of being boxed in

### Phase 4. Choose one base and treat it as scaffolding

Important mindset:

- we are borrowing structure, not inheriting product direction

### Phase 5. Rebuild the product core on top

First implement:

- schema
- seed data
- packet workflow
- findings model
- decision loop

Then layer in:

- extraction improvements
- bounded LLM assistance
- evaluation
- polished UI

## 9. How to talk about this in interviews

The correct story is not:

"I forked someone else's procurement tool."

The better story is:

"I reused commodity infrastructure for document ingestion and review UI, then designed the core data model, cross-document validation, evidence system, policy routing, and evaluation workflow for a vendor onboarding review problem."

That sounds exactly like good engineering judgment, because it is.

## 10. My recommendation

For this project, the safest and strongest path is:

- do not build every layer from zero
- do not adopt a giant domain-heavy platform
- do not anchor on a chat-with-PDF repo
- start from a light full-stack or document-review base
- build the reviewer decision system yourself

## 11. Next step

The next concrete move should be:

- define the minimum technical stack
- define the required screens
- shortlist the types of open-source bases we want to inspect

After that, we can evaluate actual candidate repos with a clear rubric instead of guessing.
