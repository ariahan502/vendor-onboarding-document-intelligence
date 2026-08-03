create table vendors (
  vendor_id text primary key,
  legal_name text not null,
  normalized_legal_name text,
  tax_id text,
  country text,
  category text,
  created_at timestamptz not null default now()
);

create table document_packages (
  package_id text primary key,
  vendor_id text not null references vendors(vendor_id),
  package_status text not null,
  submitted_at timestamptz not null default now(),
  assigned_reviewer text,
  system_recommendation text,
  final_decision text,
  priority_score int,
  notes text
);

create table document_requirements (
  requirement_id text primary key,
  package_id text not null references document_packages(package_id),
  required_doc_type text not null,
  is_required boolean not null default true,
  is_satisfied boolean not null default false,
  missing_reason text
);

create table documents (
  document_id text primary key,
  package_id text not null references document_packages(package_id),
  doc_type text not null,
  file_name text not null,
  file_path text,
  mime_type text,
  page_count int,
  document_version int not null default 1,
  upload_status text not null default 'uploaded',
  ocr_status text not null default 'pending',
  parse_status text not null default 'pending',
  uploaded_at timestamptz not null default now()
);

create table processing_runs (
  processing_run_id text primary key,
  package_id text not null references document_packages(package_id),
  document_id text references documents(document_id),
  run_type text not null,
  run_status text not null,
  model_name text,
  model_version text,
  prompt_version text,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  error_message text
);

create table extracted_fields (
  field_id text primary key,
  document_id text not null references documents(document_id),
  processing_run_id text references processing_runs(processing_run_id),
  field_name text not null,
  raw_value text,
  value_type text,
  confidence numeric(5,4),
  source_page int,
  source_span_text text,
  source_bbox jsonb,
  extracted_at timestamptz not null default now()
);

create table field_normalizations (
  normalization_id text primary key,
  field_id text not null references extracted_fields(field_id),
  normalized_value text,
  normalized_value_json jsonb,
  normalization_method text not null,
  normalization_confidence numeric(5,4),
  created_at timestamptz not null default now()
);

create table field_comparisons (
  comparison_id text primary key,
  package_id text not null references document_packages(package_id),
  left_field_id text not null references extracted_fields(field_id),
  right_field_id text not null references extracted_fields(field_id),
  comparison_type text not null,
  comparison_status text not null,
  similarity_score numeric(6,4),
  requires_review boolean not null default false,
  explanation text,
  created_at timestamptz not null default now()
);

create table policy_rules (
  rule_id text primary key,
  rule_name text not null,
  rule_code text not null unique,
  rule_description text not null,
  severity text not null,
  decision_impact text,
  condition_expression text not null,
  rule_version text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table routing_policies (
  routing_policy_id text primary key,
  policy_name text not null,
  policy_version text not null,
  description text,
  routing_expression text not null,
  created_at timestamptz not null default now()
);

create table validation_findings (
  finding_id text primary key,
  package_id text not null references document_packages(package_id),
  document_id text references documents(document_id),
  comparison_id text references field_comparisons(comparison_id),
  rule_id text references policy_rules(rule_id),
  finding_type text not null,
  severity text not null,
  finding_status text not null default 'open',
  title text not null,
  description text not null,
  suggested_action text,
  requires_human_review boolean not null default false,
  created_at timestamptz not null default now()
);

create table decision_evidence (
  evidence_id text primary key,
  package_id text not null references document_packages(package_id),
  finding_id text references validation_findings(finding_id),
  field_id text references extracted_fields(field_id),
  document_id text references documents(document_id),
  evidence_type text not null,
  page_num int,
  snippet_text text,
  bbox jsonb,
  created_at timestamptz not null default now()
);

create table review_decisions (
  decision_id text primary key,
  package_id text not null references document_packages(package_id),
  reviewer text not null,
  system_recommendation text,
  final_decision text not null,
  override_reason text,
  reviewer_comment text,
  decision_at timestamptz not null default now()
);

-- Application-level append-only ledger. Exported hashes allow an external archive
-- to verify ordering and detect edits to a saved audit stream.
create table audit_events (
  event_id text primary key,
  actor_id text not null,
  actor_role text not null,
  action text not null,
  package_id text,
  resource_type text not null,
  resource_id text,
  event_metadata jsonb,
  previous_event_hash text,
  event_hash text not null unique,
  created_at timestamptz not null
);

create table evaluation_cases (
  eval_case_id text primary key,
  package_id text references document_packages(package_id),
  case_name text not null,
  case_slice text,
  expected_fields jsonb,
  expected_findings jsonb,
  expected_decision text,
  created_at timestamptz not null default now()
);

create table evaluation_runs (
  eval_run_id text primary key,
  eval_case_id text not null references evaluation_cases(eval_case_id),
  run_label text not null,
  model_name text,
  model_version text,
  prompt_version text,
  rule_version text,
  extraction_score numeric(6,4),
  finding_score numeric(6,4),
  routing_score numeric(6,4),
  reviewer_agreement_score numeric(6,4),
  run_started_at timestamptz not null default now(),
  run_completed_at timestamptz,
  notes text
);

create index idx_document_packages_vendor_id
  on document_packages(vendor_id);

create index idx_documents_package_id
  on documents(package_id);

create index idx_extracted_fields_document_id
  on extracted_fields(document_id);

create index idx_field_comparisons_package_id
  on field_comparisons(package_id);

create index idx_validation_findings_package_id
  on validation_findings(package_id);

create index idx_decision_evidence_package_id
  on decision_evidence(package_id);

create index idx_review_decisions_package_id
  on review_decisions(package_id);

create index idx_audit_events_actor_id
  on audit_events(actor_id);

create index idx_audit_events_package_id
  on audit_events(package_id);

create index idx_evaluation_runs_case_id
  on evaluation_runs(eval_case_id);
