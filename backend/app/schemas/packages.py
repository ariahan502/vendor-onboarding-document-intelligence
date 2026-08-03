from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PackageQueueItem(BaseModel):
    package_id: str
    vendor_id: str
    vendor_name: str
    submission_date: datetime
    package_status: str
    recommendation_status: str | None
    final_decision: str | None
    highest_severity: str | None
    finding_count: int
    ocr_required_document_count: int
    primary_finding_type: str | None
    primary_finding_title: str | None
    missing_required_documents: list[str]
    assigned_reviewer: str | None
    latest_reviewer_comment: str | None
    latest_decision_at: datetime | None


class PackageQueueResponse(BaseModel):
    items: list[PackageQueueItem]


class DocumentRequirementSummary(BaseModel):
    required_doc_type: str
    is_required: bool
    is_satisfied: bool
    missing_reason: str | None


class DocumentSummary(BaseModel):
    document_id: str
    doc_type: str
    file_name: str
    file_path: str | None
    mime_type: str | None
    upload_status: str
    ocr_status: str
    parse_status: str
    page_count: int | None


class ExtractedFieldSummary(BaseModel):
    field_id: str = ""
    field_name: str
    raw_value: str | None
    normalized_value: str | None
    confidence: float | None
    source_document_id: str
    source_page: int | None


class FindingSummary(BaseModel):
    finding_id: str
    finding_type: str
    severity: str
    title: str
    description: str
    suggested_action: str | None
    requires_human_review: bool
    finding_status: str = "open"


class EvidenceSummary(BaseModel):
    evidence_id: str
    evidence_type: str
    document_id: str
    document_name: str
    page_num: int | None
    snippet_text: str | None
    related_finding_id: str | None


class ReviewDecisionSummary(BaseModel):
    decision_id: str
    reviewer: str
    system_recommendation: str | None
    final_decision: str
    override_reason: str | None
    reviewer_comment: str | None
    decision_at: datetime


class ProcessingRunSummary(BaseModel):
    processing_run_id: str
    run_type: str
    run_status: str
    document_id: str | None
    document_name: str | None
    model_name: str | None
    prompt_version: str | None
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None


class FieldReviewOverrideSummary(BaseModel):
    override_id: str
    field_id: str
    reviewer: str
    original_value: str | None
    corrected_value: str
    correction_reason: str
    created_at: datetime


class FindingResolutionSummary(BaseModel):
    resolution_id: str
    finding_id: str
    reviewer: str
    resolution_status: str
    resolution_note: str
    created_at: datetime


class PackageDetailResponse(BaseModel):
    package_id: str
    vendor_id: str
    vendor_name: str
    package_status: str
    submitted_at: datetime
    assigned_reviewer: str | None
    system_recommendation: str | None
    final_decision: str | None
    priority_score: int | None
    notes: str | None
    requirements: list[DocumentRequirementSummary]
    documents: list[DocumentSummary]
    extracted_fields: list[ExtractedFieldSummary]
    field_overrides: list[FieldReviewOverrideSummary] = Field(default_factory=list)
    finding_resolutions: list[FindingResolutionSummary] = Field(default_factory=list)
    findings: list[FindingSummary]
    evidence: list[EvidenceSummary]
    review_history: list[ReviewDecisionSummary]
    processing_runs: list[ProcessingRunSummary]


class ReviewDecisionCreateRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)
    final_decision: str = Field(min_length=1, max_length=60)
    reviewer_comment: str | None = Field(default=None, max_length=2000)
    override_reason: str | None = Field(default=None, max_length=1000)


class ReviewDecisionCreateResponse(BaseModel):
    decision_id: str
    package_id: str
    final_decision: str
    package_status: str


class FieldReviewOverrideCreateRequest(BaseModel):
    field_id: str = Field(min_length=1, max_length=120)
    reviewer: str = Field(min_length=1, max_length=120)
    corrected_value: str = Field(min_length=1, max_length=2000)
    correction_reason: str = Field(min_length=3, max_length=2000)


class FieldReviewOverrideCreateResponse(BaseModel):
    override_id: str
    package_id: str
    field_id: str


class FindingResolutionCreateRequest(BaseModel):
    finding_id: str = Field(min_length=1, max_length=120)
    reviewer: str = Field(min_length=1, max_length=120)
    resolution_status: Literal["resolved", "accepted_risk", "not_applicable"]
    resolution_note: str = Field(min_length=3, max_length=2000)


class FindingResolutionCreateResponse(BaseModel):
    resolution_id: str
    package_id: str
    finding_id: str
    finding_status: str


class SubmittedDocumentInput(BaseModel):
    doc_type: str = Field(min_length=1, max_length=80)
    file_name: str = Field(min_length=1, max_length=255)


class PackageCreateRequest(BaseModel):
    vendor_name: str = Field(min_length=1, max_length=255)
    tax_id: str | None = Field(default=None, max_length=60)
    country: str | None = Field(default="US", max_length=60)
    category: str | None = Field(default=None, max_length=120)
    assigned_reviewer: str | None = Field(default=None, max_length=120)
    submitted_documents: list[SubmittedDocumentInput] = Field(default_factory=list)


class PackageCreateResponse(BaseModel):
    package_id: str
    vendor_id: str
    package_status: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    package_id: str
    doc_type: str
    file_name: str
    file_path: str
    page_count: int | None
    parse_status: str


class PackageSimulationResponse(BaseModel):
    package_id: str
    package_status: str
    system_recommendation: str | None
    finding_count: int
