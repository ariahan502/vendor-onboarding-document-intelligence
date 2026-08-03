export type PackageQueueItem = {
  package_id: string;
  vendor_id: string;
  vendor_name: string;
  submission_date: string;
  package_status: string;
  recommendation_status: string | null;
  final_decision: string | null;
  highest_severity: string | null;
  finding_count: number;
  ocr_required_document_count: number;
  primary_finding_type: string | null;
  primary_finding_title: string | null;
  missing_required_documents: string[];
  assigned_reviewer: string | null;
  latest_reviewer_comment: string | null;
  latest_decision_at: string | null;
};

export type PackageQueueResponse = {
  items: PackageQueueItem[];
};

export type DocumentRequirementSummary = {
  required_doc_type: string;
  is_required: boolean;
  is_satisfied: boolean;
  missing_reason: string | null;
};

export type DocumentSummary = {
  document_id: string;
  doc_type: string;
  file_name: string;
  file_path: string | null;
  mime_type: string | null;
  upload_status: string;
  ocr_status: string;
  parse_status: string;
  page_count: number | null;
};

export type ExtractedFieldSummary = {
  field_id: string;
  field_name: string;
  raw_value: string | null;
  normalized_value: string | null;
  confidence: number | null;
  source_document_id: string;
  source_page: number | null;
};

export type FieldReviewOverrideSummary = {
  override_id: string;
  field_id: string;
  reviewer: string;
  original_value: string | null;
  corrected_value: string;
  correction_reason: string;
  created_at: string;
};

export type FindingSummary = {
  finding_id: string;
  finding_type: string;
  severity: string;
  title: string;
  description: string;
  suggested_action: string | null;
  requires_human_review: boolean;
  finding_status: string;
};

export type FindingResolutionSummary = {
  resolution_id: string;
  finding_id: string;
  reviewer: string;
  resolution_status: string;
  resolution_note: string;
  created_at: string;
};

export type EvidenceSummary = {
  evidence_id: string;
  evidence_type: string;
  document_id: string;
  document_name: string;
  page_num: number | null;
  snippet_text: string | null;
  related_finding_id: string | null;
};

export type ReviewDecisionSummary = {
  decision_id: string;
  reviewer: string;
  system_recommendation: string | null;
  final_decision: string;
  override_reason: string | null;
  reviewer_comment: string | null;
  decision_at: string;
};

export type ProcessingRunSummary = {
  processing_run_id: string;
  run_type: string;
  run_status: string;
  document_id: string | null;
  document_name: string | null;
  model_name: string | null;
  prompt_version: string | null;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
};

export type PackageDetailResponse = {
  package_id: string;
  vendor_id: string;
  vendor_name: string;
  package_status: string;
  submitted_at: string;
  assigned_reviewer: string | null;
  system_recommendation: string | null;
  final_decision: string | null;
  priority_score: number | null;
  notes: string | null;
  requirements: DocumentRequirementSummary[];
  documents: DocumentSummary[];
  extracted_fields: ExtractedFieldSummary[];
  field_overrides: FieldReviewOverrideSummary[];
  finding_resolutions: FindingResolutionSummary[];
  findings: FindingSummary[];
  evidence: EvidenceSummary[];
  review_history: ReviewDecisionSummary[];
  processing_runs: ProcessingRunSummary[];
};

export type ReviewDecisionCreateRequest = {
  reviewer: string;
  final_decision: string;
  reviewer_comment: string | null;
  override_reason: string | null;
};

export type ReviewDecisionCreateResponse = {
  decision_id: string;
  package_id: string;
  final_decision: string;
  package_status: string;
};

export type FieldReviewOverrideCreateRequest = {
  field_id: string;
  reviewer: string;
  corrected_value: string;
  correction_reason: string;
};

export type FieldReviewOverrideCreateResponse = {
  override_id: string;
  package_id: string;
  field_id: string;
};

export type FindingResolutionCreateRequest = {
  finding_id: string;
  reviewer: string;
  resolution_status: "resolved" | "accepted_risk" | "not_applicable";
  resolution_note: string;
};

export type FindingResolutionCreateResponse = {
  resolution_id: string;
  package_id: string;
  finding_id: string;
  finding_status: string;
};

export type SubmittedDocumentInput = {
  doc_type: string;
  file_name: string;
};

export type PackageCreateRequest = {
  vendor_name: string;
  tax_id: string | null;
  country: string | null;
  category: string | null;
  assigned_reviewer: string | null;
  submitted_documents: SubmittedDocumentInput[];
};

export type PackageCreateResponse = {
  package_id: string;
  vendor_id: string;
  package_status: string;
};

export type DocumentUploadResponse = {
  document_id: string;
  package_id: string;
  doc_type: string;
  file_name: string;
  file_path: string;
  page_count: number | null;
  parse_status: string;
};

export type PackageSimulationResponse = {
  package_id: string;
  package_status: string;
  system_recommendation: string | null;
  finding_count: number;
};
