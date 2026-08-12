from datetime import datetime, timezone
from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import re
from uuid import uuid4

from fastapi import HTTPException, status
from pypdf import PdfReader
from sqlalchemy import Select, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.decisioning import (
    DecisionEvidence,
    FieldReviewOverride,
    FindingResolution,
    ReviewDecision,
    ValidationFinding,
)
from app.models.documents import Document, DocumentPackage, DocumentRequirement, Vendor
from app.models.processing import ExtractedField, FieldNormalization, OcrPageText, ProcessingRun
from app.config import settings
from app.services.storage import (
    StorageConfigurationError,
    build_document_key,
    get_document_storage,
    legacy_local_document_key,
)
from app.schemas.packages import (
    PackageCreateRequest,
    PackageCreateResponse,
    DocumentRequirementSummary,
    DocumentSummary,
    EvidenceSummary,
    ExtractedFieldSummary,
    FieldReviewOverrideCreateRequest,
    FieldReviewOverrideCreateResponse,
    FieldReviewOverrideSummary,
    FindingResolutionCreateRequest,
    FindingResolutionCreateResponse,
    FindingResolutionSummary,
    FindingSummary,
    PackageDetailResponse,
    PackageQueueItem,
    PackageQueueResponse,
    PackageSimulationResponse,
    DocumentUploadResponse,
    ProcessingRunSummary,
    ReviewDecisionCreateRequest,
    ReviewDecisionCreateResponse,
    ReviewDecisionSummary,
)


SAMPLE_PACKAGE_DETAILS: dict[str, PackageDetailResponse] = {
    "pkg_1001": PackageDetailResponse(
        package_id="pkg_1001",
        vendor_id="ven_abc_consulting",
        vendor_name="ABC Consulting LLC",
        package_status="ready_for_review",
        submitted_at=datetime.fromisoformat("2026-07-28T10:15:00"),
        assigned_reviewer="aria.han",
        system_recommendation="needs_review",
        final_decision=None,
        priority_score=82,
        notes="Insurance and naming issues need reviewer confirmation.",
        requirements=[
            DocumentRequirementSummary(
                required_doc_type="contract",
                is_required=True,
                is_satisfied=True,
                missing_reason=None,
            ),
            DocumentRequirementSummary(
                required_doc_type="w9",
                is_required=True,
                is_satisfied=True,
                missing_reason=None,
            ),
            DocumentRequirementSummary(
                required_doc_type="insurance_certificate",
                is_required=True,
                is_satisfied=True,
                missing_reason=None,
            ),
            DocumentRequirementSummary(
                required_doc_type="vendor_registration_form",
                is_required=False,
                is_satisfied=False,
                missing_reason="Optional in MVP workflow.",
            ),
        ],
        documents=[
            DocumentSummary(
                document_id="doc_contract_001",
                doc_type="contract",
                file_name="ABC_Master_Services_Agreement.pdf",
                file_path="/sample-documents/ABC_Master_Services_Agreement.pdf",
                mime_type="application/pdf",
                upload_status="uploaded",
                ocr_status="completed",
                parse_status="completed",
                page_count=1,
            ),
            DocumentSummary(
                document_id="doc_w9_001",
                doc_type="w9",
                file_name="ABC_W9.pdf",
                file_path="/sample-documents/ABC_W9.pdf",
                mime_type="application/pdf",
                upload_status="uploaded",
                ocr_status="completed",
                parse_status="completed",
                page_count=1,
            ),
            DocumentSummary(
                document_id="doc_insurance_001",
                doc_type="insurance_certificate",
                file_name="ABC_Insurance_Certificate.pdf",
                file_path="/sample-documents/ABC_Insurance_Certificate.pdf",
                mime_type="application/pdf",
                upload_status="uploaded",
                ocr_status="completed",
                parse_status="completed",
                page_count=1,
            ),
        ],
        extracted_fields=[
            ExtractedFieldSummary(
                field_name="vendor_legal_name",
                raw_value="ABC Consulting Group LLC",
                normalized_value="abc consulting group",
                confidence=0.97,
                source_document_id="doc_contract_001",
                source_page=1,
            ),
            ExtractedFieldSummary(
                field_name="vendor_legal_name",
                raw_value="ABC Consulting LLC",
                normalized_value="abc consulting",
                confidence=0.99,
                source_document_id="doc_w9_001",
                source_page=1,
            ),
            ExtractedFieldSummary(
                field_name="tax_id",
                raw_value="12-3456789",
                normalized_value="123456789",
                confidence=0.99,
                source_document_id="doc_w9_001",
                source_page=1,
            ),
            ExtractedFieldSummary(
                field_name="insurance_coverage",
                raw_value="$500,000",
                normalized_value="500000",
                confidence=0.96,
                source_document_id="doc_insurance_001",
                source_page=1,
            ),
            ExtractedFieldSummary(
                field_name="payment_terms",
                raw_value="Net 60",
                normalized_value="60",
                confidence=0.91,
                source_document_id="doc_contract_001",
                source_page=1,
            ),
        ],
        findings=[
            FindingSummary(
                finding_id="finding_name_mismatch_001",
                finding_type="cross_document_mismatch",
                severity="medium",
                title="Vendor legal name mismatch across contract and W-9",
                description=(
                    "The contract references 'ABC Consulting Group LLC' while the W-9 "
                    "references 'ABC Consulting LLC'."
                ),
                suggested_action="Confirm whether both names refer to the same legal entity.",
                requires_human_review=True,
            ),
            FindingSummary(
                finding_id="finding_insurance_coverage_001",
                finding_type="policy_violation",
                severity="high",
                title="Insurance coverage below minimum threshold",
                description=(
                    "Extracted insurance coverage is $500,000, below the minimum "
                    "required threshold of $1,000,000."
                ),
                suggested_action="Request updated insurance certificate or escalate.",
                requires_human_review=True,
            ),
            FindingSummary(
                finding_id="finding_payment_terms_001",
                finding_type="policy_violation",
                severity="medium",
                title="Payment terms may exceed standard policy limit",
                description="The contract appears to specify Net 60 terms.",
                suggested_action="Confirm whether exception approval exists.",
                requires_human_review=True,
            ),
        ],
        evidence=[
            EvidenceSummary(
                evidence_id="ev_001",
                evidence_type="snippet",
                document_id="doc_contract_001",
                document_name="ABC_Master_Services_Agreement.pdf",
                page_num=1,
                snippet_text="This Master Services Agreement is entered into by ABC Consulting Group LLC...",
                related_finding_id="finding_name_mismatch_001",
            ),
            EvidenceSummary(
                evidence_id="ev_002",
                evidence_type="snippet",
                document_id="doc_w9_001",
                document_name="ABC_W9.pdf",
                page_num=1,
                snippet_text="Business name: ABC Consulting LLC",
                related_finding_id="finding_name_mismatch_001",
            ),
            EvidenceSummary(
                evidence_id="ev_003",
                evidence_type="snippet",
                document_id="doc_insurance_001",
                document_name="ABC_Insurance_Certificate.pdf",
                page_num=1,
                snippet_text="General Liability: $500,000",
                related_finding_id="finding_insurance_coverage_001",
            ),
        ],
        review_history=[
            ReviewDecisionSummary(
                decision_id="decision_prev_001",
                reviewer="system_seed",
                system_recommendation="needs_review",
                final_decision="needs_review",
                override_reason=None,
                reviewer_comment="Seed case for MVP development and early UI work.",
                decision_at=datetime.fromisoformat("2026-07-28T10:25:00"),
            )
        ],
        processing_runs=[
            ProcessingRunSummary(
                processing_run_id="run_pkg_1001_ingest",
                run_type="ingestion",
                run_status="completed",
                document_id=None,
                document_name=None,
                model_name=None,
                prompt_version=None,
                started_at=datetime.fromisoformat("2026-07-28T10:15:20"),
                completed_at=datetime.fromisoformat("2026-07-28T10:15:45"),
                error_message=None,
            ),
            ProcessingRunSummary(
                processing_run_id="run_doc_contract_ocr",
                run_type="ocr",
                run_status="completed",
                document_id="doc_contract_001",
                document_name="ABC_Master_Services_Agreement.pdf",
                model_name="azure-document-intelligence",
                prompt_version=None,
                started_at=datetime.fromisoformat("2026-07-28T10:16:05"),
                completed_at=datetime.fromisoformat("2026-07-28T10:16:40"),
                error_message=None,
            ),
            ProcessingRunSummary(
                processing_run_id="run_doc_w9_extract",
                run_type="field_extraction",
                run_status="completed",
                document_id="doc_w9_001",
                document_name="ABC_W9.pdf",
                model_name="gpt-4.1-mini",
                prompt_version="extract-v1",
                started_at=datetime.fromisoformat("2026-07-28T10:17:10"),
                completed_at=datetime.fromisoformat("2026-07-28T10:17:45"),
                error_message=None,
            ),
            ProcessingRunSummary(
                processing_run_id="run_pkg_1001_policy",
                run_type="policy_validation",
                run_status="completed",
                document_id=None,
                document_name=None,
                model_name="rules-engine",
                prompt_version="policy-v1",
                started_at=datetime.fromisoformat("2026-07-28T10:18:00"),
                completed_at=datetime.fromisoformat("2026-07-28T10:18:12"),
                error_message=None,
            ),
        ],
    ),
    "pkg_1002": PackageDetailResponse(
        package_id="pkg_1002",
        vendor_id="ven_blue_peak",
        vendor_name="Blue Peak Analytics Inc.",
        package_status="processing",
        submitted_at=datetime.fromisoformat("2026-07-29T09:00:00"),
        assigned_reviewer=None,
        system_recommendation=None,
        final_decision=None,
        priority_score=35,
        notes=None,
        requirements=[],
        documents=[],
        extracted_fields=[],
        findings=[],
        evidence=[],
        review_history=[],
        processing_runs=[
            ProcessingRunSummary(
                processing_run_id="run_pkg_1002_ingest",
                run_type="ingestion",
                run_status="completed",
                document_id=None,
                document_name=None,
                model_name=None,
                prompt_version=None,
                started_at=datetime.fromisoformat("2026-07-29T09:00:15"),
                completed_at=datetime.fromisoformat("2026-07-29T09:00:40"),
                error_message=None,
            ),
            ProcessingRunSummary(
                processing_run_id="run_pkg_1002_ocr",
                run_type="ocr",
                run_status="running",
                document_id=None,
                document_name=None,
                model_name="azure-document-intelligence",
                prompt_version=None,
                started_at=datetime.fromisoformat("2026-07-29T09:01:00"),
                completed_at=None,
                error_message=None,
            ),
        ],
    ),
}

REQUIRED_DOC_TYPES = ["contract", "w9", "insurance_certificate"]
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@dataclass
class DocumentTextExtraction:
    pages: list[tuple[int, str]]
    source: str
    error_message: str | None = None


def list_package_queue(db: Session) -> PackageQueueResponse:
    try:
        rows = db.execute(
            select(DocumentPackage, Vendor)
            .join(Vendor, Vendor.vendor_id == DocumentPackage.vendor_id)
            .order_by(DocumentPackage.submitted_at.desc())
        ).all()
    except SQLAlchemyError:
        return _sample_queue_response()

    if not rows:
        return _sample_queue_response()

    package_ids = [package.package_id for package, _vendor in rows]
    finding_counts = _count_findings_by_package(db, package_ids)
    highest_severity = _highest_severity_by_package(db, package_ids)
    primary_findings = _primary_finding_by_package(db, package_ids)
    missing_documents = _missing_required_documents_by_package(db, package_ids)
    ocr_required_counts = _ocr_required_document_count_by_package(db, package_ids)
    latest_reviews = _latest_review_by_package(db, package_ids)

    items = [
        PackageQueueItem(
            package_id=package.package_id,
            vendor_id=vendor.vendor_id,
            vendor_name=vendor.legal_name,
            submission_date=package.submitted_at,
            package_status=package.package_status,
            recommendation_status=package.system_recommendation,
            final_decision=package.final_decision,
            highest_severity=highest_severity.get(package.package_id),
            finding_count=finding_counts.get(package.package_id, 0),
            ocr_required_document_count=ocr_required_counts.get(package.package_id, 0),
            primary_finding_type=primary_findings.get(package.package_id, (None, None))[0],
            primary_finding_title=primary_findings.get(package.package_id, (None, None))[1],
            missing_required_documents=missing_documents.get(package.package_id, []),
            assigned_reviewer=package.assigned_reviewer,
            latest_reviewer_comment=latest_reviews.get(package.package_id).reviewer_comment
            if latest_reviews.get(package.package_id)
            else None,
            latest_decision_at=latest_reviews.get(package.package_id).decision_at
            if latest_reviews.get(package.package_id)
            else None,
        )
        for package, vendor in rows
    ]
    return PackageQueueResponse(items=items)


def get_package_detail(db: Session, package_id: str) -> PackageDetailResponse:
    try:
        package_row = db.execute(
            select(DocumentPackage, Vendor)
            .join(Vendor, Vendor.vendor_id == DocumentPackage.vendor_id)
            .where(DocumentPackage.package_id == package_id)
        ).first()
    except SQLAlchemyError:
        package_row = None

    if package_row is None:
        detail = SAMPLE_PACKAGE_DETAILS.get(package_id)
        if detail is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Package '{package_id}' was not found.",
            )
        return detail

    package, vendor = package_row

    requirements = [
        DocumentRequirementSummary(
            required_doc_type=requirement.required_doc_type,
            is_required=requirement.is_required,
            is_satisfied=requirement.is_satisfied,
            missing_reason=requirement.missing_reason,
        )
        for requirement in db.scalars(
            select(DocumentRequirement)
            .where(DocumentRequirement.package_id == package_id)
            .order_by(DocumentRequirement.required_doc_type.asc())
        ).all()
    ]

    documents = db.scalars(
        select(Document)
        .where(Document.package_id == package_id)
        .order_by(Document.uploaded_at.asc())
    ).all()
    document_summaries = [
        DocumentSummary(
            document_id=document.document_id,
            doc_type=document.doc_type,
            file_name=document.file_name,
            file_path=document.file_path,
            mime_type=document.mime_type,
            upload_status=document.upload_status,
            ocr_status=document.ocr_status,
            parse_status=document.parse_status,
            page_count=document.page_count,
        )
        for document in documents
    ]

    document_by_id = {document.document_id: document for document in documents}
    field_rows = db.scalars(
        select(ExtractedField)
        .join(Document, Document.document_id == ExtractedField.document_id)
        .where(Document.package_id == package_id)
        .order_by(ExtractedField.extracted_at.asc())
    ).all()
    normalizations = db.scalars(
        select(FieldNormalization)
        .join(ExtractedField, ExtractedField.field_id == FieldNormalization.field_id)
        .join(Document, Document.document_id == ExtractedField.document_id)
        .where(Document.package_id == package_id)
        .order_by(FieldNormalization.created_at.asc())
    ).all()
    normalized_by_field: dict[str, FieldNormalization] = {}
    for normalization in normalizations:
        normalized_by_field.setdefault(normalization.field_id, normalization)

    extracted_fields = [
        ExtractedFieldSummary(
            field_id=field.field_id,
            field_name=field.field_name,
            raw_value=field.raw_value,
            normalized_value=normalized_by_field.get(field.field_id).normalized_value
            if normalized_by_field.get(field.field_id)
            else None,
            confidence=_decimal_to_float(field.confidence),
            source_document_id=field.document_id,
            source_page=field.source_page,
        )
        for field in field_rows
    ]
    field_overrides = [
        FieldReviewOverrideSummary(
            override_id=override.override_id,
            field_id=override.field_id,
            reviewer=override.reviewer,
            original_value=override.original_value,
            corrected_value=override.corrected_value,
            correction_reason=override.correction_reason,
            created_at=override.created_at,
        )
        for override in db.scalars(
            select(FieldReviewOverride)
            .where(FieldReviewOverride.package_id == package_id)
            .order_by(FieldReviewOverride.created_at.desc())
        ).all()
    ]

    finding_rows = db.scalars(
        select(ValidationFinding)
        .where(ValidationFinding.package_id == package_id)
        .order_by(ValidationFinding.created_at.asc())
    ).all()
    findings = [
        FindingSummary(
            finding_id=finding.finding_id,
            finding_type=finding.finding_type,
            severity=finding.severity,
            title=finding.title,
            description=finding.description,
            suggested_action=finding.suggested_action,
            requires_human_review=finding.requires_human_review,
            finding_status=finding.finding_status,
        )
        for finding in finding_rows
    ]
    finding_resolutions = [
        FindingResolutionSummary(
            resolution_id=resolution.resolution_id,
            finding_id=resolution.finding_id,
            reviewer=resolution.reviewer,
            resolution_status=resolution.resolution_status,
            resolution_note=resolution.resolution_note,
            created_at=resolution.created_at,
        )
        for resolution in db.scalars(
            select(FindingResolution)
            .where(FindingResolution.package_id == package_id)
            .order_by(FindingResolution.created_at.desc())
        ).all()
    ]

    evidence_rows = db.execute(
        select(DecisionEvidence, Document.file_name)
        .join(Document, Document.document_id == DecisionEvidence.document_id, isouter=True)
        .where(DecisionEvidence.package_id == package_id)
        .order_by(DecisionEvidence.created_at.asc())
    ).all()
    evidence = [
        EvidenceSummary(
            evidence_id=evidence_row.evidence_id,
            evidence_type=evidence_row.evidence_type,
            document_id=evidence_row.document_id or "",
            document_name=file_name or _document_name_for(
                evidence_row.document_id, document_by_id
            ),
            page_num=evidence_row.page_num,
            snippet_text=evidence_row.snippet_text,
            related_finding_id=evidence_row.finding_id,
        )
        for evidence_row, file_name in evidence_rows
    ]

    review_history = [
        ReviewDecisionSummary(
            decision_id=decision.decision_id,
            reviewer=decision.reviewer,
            system_recommendation=decision.system_recommendation,
            final_decision=decision.final_decision,
            override_reason=decision.override_reason,
            reviewer_comment=decision.reviewer_comment,
            decision_at=decision.decision_at,
        )
        for decision in db.scalars(
            select(ReviewDecision)
            .where(ReviewDecision.package_id == package_id)
            .order_by(ReviewDecision.decision_at.desc())
        ).all()
    ]
    processing_runs = [
        ProcessingRunSummary(
            processing_run_id=run.processing_run_id,
            run_type=run.run_type,
            run_status=run.run_status,
            document_id=run.document_id,
            document_name=_document_name_for(run.document_id, document_by_id)
            if run.document_id
            else None,
            model_name=run.model_name,
            prompt_version=run.prompt_version,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_message=run.error_message,
        )
        for run in db.scalars(
            select(ProcessingRun)
            .where(ProcessingRun.package_id == package_id)
            .order_by(ProcessingRun.started_at.asc())
        ).all()
    ]

    return PackageDetailResponse(
        package_id=package.package_id,
        vendor_id=vendor.vendor_id,
        vendor_name=vendor.legal_name,
        package_status=package.package_status,
        submitted_at=package.submitted_at,
        assigned_reviewer=package.assigned_reviewer,
        system_recommendation=package.system_recommendation,
        final_decision=package.final_decision,
        priority_score=package.priority_score,
        notes=package.notes,
        requirements=requirements,
        documents=document_summaries,
        extracted_fields=extracted_fields,
        field_overrides=field_overrides,
        finding_resolutions=finding_resolutions,
        findings=findings,
        evidence=evidence,
        review_history=review_history,
        processing_runs=processing_runs,
    )


def create_package(db: Session, payload: PackageCreateRequest) -> PackageCreateResponse:
    package_id = f"pkg_{uuid4().hex[:8]}"
    vendor_id = f"ven_{uuid4().hex[:8]}"
    submitted_doc_types = {item.doc_type for item in payload.submitted_documents}

    vendor = Vendor(
        vendor_id=vendor_id,
        legal_name=payload.vendor_name,
        normalized_legal_name=payload.vendor_name.strip().lower(),
        tax_id=payload.tax_id,
        country=payload.country,
        category=payload.category,
    )
    package = DocumentPackage(
        package_id=package_id,
        vendor_id=vendor_id,
        package_status="processing",
        assigned_reviewer=payload.assigned_reviewer,
        system_recommendation=None,
        final_decision=None,
        priority_score=40 + max(0, (3 - len(submitted_doc_types)) * 10),
        notes="New packet created from the intake form and queued for processing.",
    )
    requirements = [
        DocumentRequirement(
            requirement_id=f"req_{package_id}_{doc_type}",
            package_id=package_id,
            required_doc_type=doc_type,
            is_required=True,
            is_satisfied=doc_type in submitted_doc_types,
            missing_reason=None
            if doc_type in submitted_doc_types
            else "Vendor has not submitted this required document yet.",
        )
        for doc_type in REQUIRED_DOC_TYPES
    ]
    documents = [
        Document(
            document_id=f"doc_{uuid4().hex[:10]}",
            package_id=package_id,
            doc_type=item.doc_type,
            file_name=item.file_name,
            file_path=None,
            mime_type="application/pdf",
            page_count=None,
            upload_status="uploaded",
            ocr_status="queued",
            parse_status="pending",
        )
        for item in payload.submitted_documents
    ]
    processing_runs = [
        ProcessingRun(
            processing_run_id=f"run_{uuid4().hex[:10]}",
            package_id=package_id,
            document_id=None,
            run_type="ingestion",
            run_status="queued",
            model_name=None,
            prompt_version=None,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )
    ]
    processing_runs.extend(
        ProcessingRun(
            processing_run_id=f"run_{uuid4().hex[:10]}",
            package_id=package_id,
            document_id=document.document_id,
            run_type="ocr",
            run_status="queued",
            model_name="azure-document-intelligence",
            prompt_version=None,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )
        for document in documents
    )

    try:
        db.add(vendor)
        db.add(package)
        db.add_all(requirements)
        db.add_all(documents)
        db.add_all(processing_runs)
        db.commit()
    except SQLAlchemyError:
        detail = _create_sample_package(package_id, vendor_id, payload)
        SAMPLE_PACKAGE_DETAILS[package_id] = detail
        return PackageCreateResponse(
            package_id=detail.package_id,
            vendor_id=detail.vendor_id,
            package_status=detail.package_status,
        )

    return PackageCreateResponse(
        package_id=package_id,
        vendor_id=vendor_id,
        package_status="processing",
    )


def upload_document_file(
    db: Session,
    *,
    package_id: str,
    doc_type: str,
    file_name: str,
    mime_type: str | None,
    contents: bytes,
) -> DocumentUploadResponse:
    """Validate and store one PDF, then attach it to a package document record."""
    package = _load_package_for_update(db, package_id)
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package '{package_id}' was not found.",
        )
    if doc_type not in REQUIRED_DOC_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Document type must be one of the required onboarding documents.",
        )
    if not contents or len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="PDF uploads must be between 1 byte and 10 MB.",
        )
    if not contents.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported during this MVP stage.",
        )

    try:
        reader = PdfReader(BytesIO(contents))
        page_count = len(reader.pages)
        has_extractable_text = any(
            (page.extract_text() or "").strip() for page in reader.pages
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The uploaded file is not a readable PDF.",
        ) from exc

    document = db.scalar(
        select(Document)
        .where(Document.package_id == package_id, Document.doc_type == doc_type)
        .order_by(Document.uploaded_at.asc())
    )
    if document is None:
        document = Document(
            document_id=f"doc_{uuid4().hex[:10]}",
            package_id=package_id,
            doc_type=doc_type,
            file_name=file_name,
            file_path=None,
            mime_type="application/pdf",
            page_count=page_count,
            upload_status="uploaded",
            ocr_status="not_required" if has_extractable_text else "required",
            parse_status="metadata_extracted" if has_extractable_text else "awaiting_ocr",
        )
        db.add(document)

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(file_name).name).strip("._")
    safe_name = safe_name or "uploaded-document.pdf"
    storage_key = build_document_key(package_id, document.document_id, safe_name)
    try:
        get_document_storage().write_bytes(storage_key, contents)
    except Exception as exc:
        detail = "Document storage is not configured." if isinstance(exc, StorageConfigurationError) else "Document storage is unavailable."
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail) from exc

    document.file_name = safe_name
    document.storage_key = storage_key
    document.file_path = f"/api/packages/{package_id}/documents/{document.document_id}/file"
    document.mime_type = "application/pdf"
    document.page_count = page_count
    document.upload_status = "uploaded"
    document.ocr_status = "not_required" if has_extractable_text else "required"
    document.parse_status = "metadata_extracted" if has_extractable_text else "awaiting_ocr"

    requirement = db.scalar(
        select(DocumentRequirement).where(
            DocumentRequirement.package_id == package_id,
            DocumentRequirement.required_doc_type == doc_type,
        )
    )
    if requirement is not None:
        requirement.is_satisfied = True
        requirement.missing_reason = None

    ocr_run = db.scalar(
        select(ProcessingRun).where(
            ProcessingRun.package_id == package_id,
            ProcessingRun.document_id == document.document_id,
            ProcessingRun.run_type == "ocr",
        )
    )
    if ocr_run is None:
        ocr_run = ProcessingRun(
            processing_run_id=f"run_{uuid4().hex[:10]}",
            package_id=package_id,
            document_id=document.document_id,
            run_type="ocr",
            run_status="completed" if has_extractable_text else "needs_configuration",
            model_name="text-layer" if has_extractable_text else None,
            prompt_version=None,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            error_message=(
                None
                if has_extractable_text
                else "No OCR engine is configured for scanned PDFs in local development."
            ),
        )
        db.add(ocr_run)
    else:
        ocr_run.run_status = "completed" if has_extractable_text else "needs_configuration"
        ocr_run.completed_at = datetime.now(timezone.utc)
        ocr_run.model_name = "text-layer" if has_extractable_text else None
        ocr_run.error_message = (
            None
            if has_extractable_text
            else "No OCR engine is configured for scanned PDFs in local development."
        )

    db.add(
        ProcessingRun(
            processing_run_id=f"run_{uuid4().hex[:10]}",
            package_id=package_id,
            document_id=document.document_id,
            run_type="pdf_validation",
            run_status="completed",
            model_name="pypdf",
            prompt_version=None,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    return DocumentUploadResponse(
        document_id=document.document_id,
        package_id=package_id,
        doc_type=document.doc_type,
        file_name=document.file_name,
        file_path=document.file_path,
        page_count=document.page_count,
        parse_status=document.parse_status,
    )


def get_document_file(db: Session, package_id: str, document_id: str) -> tuple[bytes, str, str]:
    """Resolve a stored file after verifying package ownership from the database."""
    document = db.scalar(
        select(Document).where(
            Document.package_id == package_id,
            Document.document_id == document_id,
        )
    )
    if document is None or not document.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found.")

    storage_key = document.storage_key or legacy_local_document_key(
        package_id, document.document_id, document.file_name
    )
    try:
        contents = get_document_storage().read_bytes(storage_key)
    except (FileNotFoundError, OSError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found.")
    return contents, document.mime_type or "application/pdf", document.file_name


def create_review_decision(
    db: Session,
    package_id: str,
    payload: ReviewDecisionCreateRequest,
) -> ReviewDecisionCreateResponse:
    package = _load_package_for_update(db, package_id)
    if package is None:
        return _create_sample_review_decision(package_id, payload)

    if payload.final_decision == "approve":
        blockers = db.scalars(
            select(ValidationFinding.title).where(
                ValidationFinding.package_id == package_id,
                ValidationFinding.finding_status == "open",
                ValidationFinding.severity.in_(["high", "critical"]),
            )
        ).all()
        if blockers and not (payload.override_reason and payload.override_reason.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "Approval requires an override reason while high-risk findings remain open: "
                    + "; ".join(blockers)
                ),
            )

    package.final_decision = payload.final_decision
    package.package_status = _package_status_for_decision(payload.final_decision)
    package.assigned_reviewer = payload.reviewer

    decision = ReviewDecision(
        decision_id=f"decision_{uuid4().hex[:12]}",
        package_id=package.package_id,
        reviewer=payload.reviewer,
        system_recommendation=package.system_recommendation,
        final_decision=payload.final_decision,
        override_reason=payload.override_reason,
        reviewer_comment=payload.reviewer_comment,
        decision_at=datetime.now(timezone.utc),
    )

    db.add(decision)
    db.commit()

    return ReviewDecisionCreateResponse(
        decision_id=decision.decision_id,
        package_id=package.package_id,
        final_decision=decision.final_decision,
        package_status=package.package_status,
    )


def create_field_review_override(
    db: Session,
    package_id: str,
    payload: FieldReviewOverrideCreateRequest,
) -> FieldReviewOverrideCreateResponse:
    field = db.scalar(
        select(ExtractedField)
        .join(Document, Document.document_id == ExtractedField.document_id)
        .where(
            ExtractedField.field_id == payload.field_id,
            Document.package_id == package_id,
        )
    )
    if field is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extracted field was not found in this package.",
        )

    override = FieldReviewOverride(
        override_id=f"override_{uuid4().hex[:12]}",
        package_id=package_id,
        field_id=field.field_id,
        reviewer=payload.reviewer,
        original_value=field.raw_value,
        corrected_value=payload.corrected_value.strip(),
        correction_reason=payload.correction_reason.strip(),
    )
    db.add(override)
    db.commit()

    return FieldReviewOverrideCreateResponse(
        override_id=override.override_id,
        package_id=package_id,
        field_id=field.field_id,
    )


def create_finding_resolution(
    db: Session,
    package_id: str,
    payload: FindingResolutionCreateRequest,
) -> FindingResolutionCreateResponse:
    finding = db.scalar(
        select(ValidationFinding).where(
            ValidationFinding.package_id == package_id,
            ValidationFinding.finding_id == payload.finding_id,
        )
    )
    if finding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding was not found in this package.",
        )

    finding.finding_status = payload.resolution_status
    resolution = FindingResolution(
        resolution_id=f"resolution_{uuid4().hex[:12]}",
        package_id=package_id,
        finding_id=finding.finding_id,
        reviewer=payload.reviewer,
        resolution_status=payload.resolution_status,
        resolution_note=payload.resolution_note.strip(),
    )
    db.add(resolution)
    db.commit()

    return FindingResolutionCreateResponse(
        resolution_id=resolution.resolution_id,
        package_id=package_id,
        finding_id=finding.finding_id,
        finding_status=finding.finding_status,
    )


def simulate_package_processing(
    db: Session, package_id: str
) -> PackageSimulationResponse:
    package = _load_package_for_update(db, package_id)
    if package is None:
        return _simulate_sample_package_processing(package_id)

    documents = db.scalars(
        select(Document)
        .where(Document.package_id == package_id)
        .order_by(Document.uploaded_at.asc())
    ).all()
    requirements = db.scalars(
        select(DocumentRequirement).where(DocumentRequirement.package_id == package_id)
    ).all()

    submitted_doc_types = {document.doc_type for document in documents}
    ocr_required_document_ids: set[str] = set()
    ocr_completed_document_ids: set[str] = set()
    text_extractions = {
        document.document_id: _extract_uploaded_pdf_text(document)
        for document in documents
    }
    for document in documents:
        document.upload_status = "uploaded"
        text_extraction = text_extractions[document.document_id]
        if text_extraction is not None and not text_extraction.pages:
            document.ocr_status = "required"
            document.parse_status = "awaiting_ocr"
            ocr_required_document_ids.add(document.document_id)
        else:
            document.ocr_status = (
                "completed"
                if text_extraction is not None and text_extraction.source == "azure_ai_document_intelligence"
                else "not_required"
                if text_extraction is not None
                else "completed"
            )
            document.parse_status = "completed"
            if text_extraction is not None and text_extraction.source == "azure_ai_document_intelligence":
                ocr_completed_document_ids.add(document.document_id)

    for requirement in requirements:
        requirement.is_satisfied = requirement.required_doc_type in submitted_doc_types
        requirement.missing_reason = (
            None
            if requirement.is_satisfied
            else "Vendor has not submitted this required document yet."
        )

    existing_evidence = db.scalars(
        select(DecisionEvidence).where(DecisionEvidence.package_id == package_id)
    ).all()
    for evidence in existing_evidence:
        db.delete(evidence)

    for artifact in db.scalars(
        select(OcrPageText).join(Document).where(Document.package_id == package_id)
    ).all():
        db.delete(artifact)

    existing_resolutions = db.scalars(
        select(FindingResolution).where(FindingResolution.package_id == package_id)
    ).all()
    for resolution in existing_resolutions:
        db.delete(resolution)

    existing_findings = db.scalars(
        select(ValidationFinding).where(ValidationFinding.package_id == package_id)
    ).all()
    for finding in existing_findings:
        db.delete(finding)

    existing_fields = db.scalars(
        select(ExtractedField)
        .join(Document, Document.document_id == ExtractedField.document_id)
        .where(Document.package_id == package_id)
    ).all()
    existing_field_ids = [field.field_id for field in existing_fields]
    if existing_field_ids:
        for normalization in db.scalars(
            select(FieldNormalization).where(
                FieldNormalization.field_id.in_(existing_field_ids)
            )
        ).all():
            db.delete(normalization)
        for field in existing_fields:
            db.delete(field)

    extraction_run_id = _complete_processing_runs(
        db,
        package_id,
        documents,
        ocr_required_document_ids,
        ocr_completed_document_ids,
    )
    for document in documents:
        extraction = text_extractions[document.document_id]
        if extraction is not None:
            for page_number, text_content in extraction.pages:
                db.add(OcrPageText(
                    ocr_page_text_id=f"ocrtext_{uuid4().hex[:12]}",
                    document_id=document.document_id,
                    processing_run_id=extraction_run_id,
                    page_number=page_number,
                    source=extraction.source,
                    text_content=text_content,
                ))
    extracted_fields, normalizations = _build_processing_fields(
        package, documents, extraction_run_id, text_extractions
    )
    for field in extracted_fields:
        db.add(field)
    for normalization in normalizations:
        db.add(normalization)
    findings = _build_processing_findings(
        package, documents, requirements, extracted_fields
    )
    for finding in findings:
        db.add(finding)
    evidence = _build_processing_evidence(findings, extracted_fields, documents)
    for item in evidence:
        db.add(item)

    package.package_status = "ready_for_review"
    package.system_recommendation = "approve" if not findings else "needs_review"
    package.priority_score = 25 if not findings else 70
    package.notes = (
        "Packet completed automated processing with no blocking findings."
        if not findings
        else "Packet completed automated processing and surfaced findings for reviewer confirmation."
    )

    db.commit()

    return PackageSimulationResponse(
        package_id=package.package_id,
        package_status=package.package_status,
        system_recommendation=package.system_recommendation,
        finding_count=len(findings),
    )


def process_next_queued_package(db: Session) -> PackageSimulationResponse | None:
    """Claim the oldest processing packet for the local worker loop."""
    package_id = db.scalar(
        select(DocumentPackage.package_id)
        .where(DocumentPackage.package_status == "processing")
        .order_by(DocumentPackage.submitted_at.asc())
        .limit(1)
    )
    if package_id is None:
        return None
    return simulate_package_processing(db, package_id)


def _highest_severity(findings: list[FindingSummary]) -> str | None:
    if not findings:
        return None

    order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    ranked = max(findings, key=lambda finding: order.get(finding.severity, 0))
    return ranked.severity


def _sample_queue_response() -> PackageQueueResponse:
    items = [
        PackageQueueItem(
            package_id=detail.package_id,
            vendor_id=detail.vendor_id,
            vendor_name=detail.vendor_name,
            submission_date=detail.submitted_at,
            package_status=detail.package_status,
            recommendation_status=detail.system_recommendation,
            final_decision=detail.final_decision,
            highest_severity=_highest_severity(detail.findings),
            finding_count=len(detail.findings),
            ocr_required_document_count=sum(
                document.ocr_status == "required" for document in detail.documents
            ),
            primary_finding_type=_primary_sample_finding(detail.findings).finding_type
            if _primary_sample_finding(detail.findings)
            else None,
            primary_finding_title=_primary_sample_finding(detail.findings).title
            if _primary_sample_finding(detail.findings)
            else None,
            missing_required_documents=[
                req.required_doc_type
                for req in detail.requirements
                if req.is_required and not req.is_satisfied
            ],
            assigned_reviewer=detail.assigned_reviewer,
            latest_reviewer_comment=detail.review_history[0].reviewer_comment
            if detail.review_history
            else None,
            latest_decision_at=detail.review_history[0].decision_at
            if detail.review_history
            else None,
        )
        for detail in SAMPLE_PACKAGE_DETAILS.values()
    ]
    items.sort(key=lambda item: item.submission_date, reverse=True)
    return PackageQueueResponse(items=items)


def _load_package_for_update(db: Session, package_id: str) -> DocumentPackage | None:
    try:
        return db.scalar(
            select(DocumentPackage).where(DocumentPackage.package_id == package_id)
        )
    except SQLAlchemyError:
        return None


def _create_sample_review_decision(
    package_id: str, payload: ReviewDecisionCreateRequest
) -> ReviewDecisionCreateResponse:
    detail = SAMPLE_PACKAGE_DETAILS.get(package_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package '{package_id}' was not found.",
        )

    detail.final_decision = payload.final_decision
    detail.package_status = _package_status_for_decision(payload.final_decision)
    detail.assigned_reviewer = payload.reviewer
    detail.review_history.insert(
        0,
        ReviewDecisionSummary(
            decision_id=f"decision_{uuid4().hex[:12]}",
            reviewer=payload.reviewer,
            system_recommendation=detail.system_recommendation,
            final_decision=payload.final_decision,
            override_reason=payload.override_reason,
            reviewer_comment=payload.reviewer_comment,
            decision_at=datetime.now(timezone.utc),
        ),
    )

    return ReviewDecisionCreateResponse(
        decision_id=detail.review_history[0].decision_id,
        package_id=package_id,
        final_decision=payload.final_decision,
        package_status=detail.package_status,
    )


def _count_findings_by_package(db: Session, package_ids: list[str]) -> dict[str, int]:
    rows = db.execute(
        select(
            ValidationFinding.package_id,
            func.count(ValidationFinding.finding_id),
        )
        .where(
            ValidationFinding.package_id.in_(package_ids),
            ValidationFinding.finding_status == "open",
        )
        .group_by(ValidationFinding.package_id)
    ).all()
    return {package_id: count for package_id, count in rows}


def _highest_severity_by_package(
    db: Session, package_ids: list[str]
) -> dict[str, str | None]:
    rows = db.execute(
        select(
            ValidationFinding.package_id,
            ValidationFinding.severity,
        ).where(
            ValidationFinding.package_id.in_(package_ids),
            ValidationFinding.finding_status == "open",
        )
    ).all()
    order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    highest: dict[str, str | None] = {}
    for package_id, severity in rows:
        current = highest.get(package_id)
        if current is None or order.get(severity, 0) > order.get(current, 0):
            highest[package_id] = severity
    return highest


def _primary_finding_by_package(
    db: Session, package_ids: list[str]
) -> dict[str, tuple[str, str]]:
    rows = db.scalars(
        select(ValidationFinding).where(
            ValidationFinding.package_id.in_(package_ids),
            ValidationFinding.finding_status == "open",
        )
    ).all()
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    primary: dict[str, ValidationFinding] = {}
    for row in rows:
        current = primary.get(row.package_id)
        if current is None or (
            severity_order.get(row.severity, 0), row.requires_human_review, row.created_at
        ) > (
            severity_order.get(current.severity, 0),
            current.requires_human_review,
            current.created_at,
        ):
            primary[row.package_id] = row
    return {
        package_id: (finding.finding_type, finding.title)
        for package_id, finding in primary.items()
    }


def _primary_sample_finding(findings: list[FindingSummary]) -> FindingSummary | None:
    if not findings:
        return None
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    return max(
        findings,
        key=lambda finding: (
            severity_order.get(finding.severity, 0),
            finding.requires_human_review,
        ),
    )


def _missing_required_documents_by_package(
    db: Session, package_ids: list[str]
) -> dict[str, list[str]]:
    rows = db.scalars(
        select(DocumentRequirement)
        .where(
            DocumentRequirement.package_id.in_(package_ids),
            DocumentRequirement.is_required.is_(True),
            DocumentRequirement.is_satisfied.is_(False),
        )
        .order_by(DocumentRequirement.required_doc_type.asc())
    ).all()
    missing: dict[str, list[str]] = {package_id: [] for package_id in package_ids}
    for row in rows:
        missing.setdefault(row.package_id, []).append(row.required_doc_type)
    return missing


def _ocr_required_document_count_by_package(
    db: Session, package_ids: list[str]
) -> dict[str, int]:
    rows = db.execute(
        select(Document.package_id, func.count(Document.document_id))
        .where(
            Document.package_id.in_(package_ids),
            Document.ocr_status == "required",
        )
        .group_by(Document.package_id)
    ).all()
    return {package_id: count for package_id, count in rows}


def _latest_review_by_package(
    db: Session, package_ids: list[str]
) -> dict[str, ReviewDecision]:
    rows = db.scalars(
        select(ReviewDecision)
        .where(ReviewDecision.package_id.in_(package_ids))
        .order_by(ReviewDecision.package_id.asc(), ReviewDecision.decision_at.desc())
    ).all()
    latest: dict[str, ReviewDecision] = {}
    for row in rows:
        latest.setdefault(row.package_id, row)
    return latest


def _document_name_for(document_id: str | None, documents: dict[str, Document]) -> str:
    if document_id is None:
        return "Unknown document"
    document = documents.get(document_id)
    return document.file_name if document else "Unknown document"


def _decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _package_status_for_decision(final_decision: str) -> str:
    mapping = {
        "approve": "approved",
        "needs_review": "ready_for_review",
        "request_resubmission": "needs_vendor_resubmission",
        "escalate": "escalated",
        "reject": "rejected",
    }
    return mapping.get(final_decision, "ready_for_review")


def _simulate_sample_package_processing(
    package_id: str,
) -> PackageSimulationResponse:
    detail = SAMPLE_PACKAGE_DETAILS.get(package_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package '{package_id}' was not found.",
        )

    submitted_doc_types = {document.doc_type for document in detail.documents}
    for document in detail.documents:
        document.ocr_status = "completed"
        document.parse_status = "completed"

    for requirement in detail.requirements:
        requirement.is_satisfied = requirement.required_doc_type in submitted_doc_types
        requirement.missing_reason = (
            None
            if requirement.is_satisfied
            else "Vendor has not submitted this required document yet."
        )

    detail.extracted_fields = _build_sample_processing_fields(
        detail.vendor_name, detail.documents
    )
    detail.findings = _build_sample_processing_findings(
        detail.package_id,
        detail.vendor_name,
        detail.documents,
        detail.requirements,
        detail.extracted_fields,
    )
    detail.evidence = _build_sample_processing_evidence(
        detail.findings, detail.extracted_fields, detail.documents
    )
    detail.processing_runs = [
        ProcessingRunSummary(
            processing_run_id=run.processing_run_id,
            run_type=run.run_type,
            run_status="completed" if run.run_status == "running" else run.run_status,
            document_id=run.document_id,
            document_name=run.document_name,
            model_name=run.model_name,
            prompt_version=run.prompt_version,
            started_at=run.started_at,
            completed_at=run.completed_at or datetime.now(timezone.utc),
            error_message=run.error_message,
        )
        for run in detail.processing_runs
    ]
    detail.package_status = "ready_for_review"
    detail.system_recommendation = "approve" if not detail.findings else "needs_review"
    detail.priority_score = 25 if not detail.findings else 70
    detail.notes = (
        "Packet completed automated processing with no blocking findings."
        if not detail.findings
        else "Packet completed automated processing and surfaced findings for reviewer confirmation."
    )

    return PackageSimulationResponse(
        package_id=detail.package_id,
        package_status=detail.package_status,
        system_recommendation=detail.system_recommendation,
        finding_count=len(detail.findings),
    )


def _create_sample_package(
    package_id: str, vendor_id: str, payload: PackageCreateRequest
) -> PackageDetailResponse:
    submitted_doc_types = {item.doc_type for item in payload.submitted_documents}
    documents = [
        DocumentSummary(
            document_id=f"doc_{uuid4().hex[:10]}",
            doc_type=item.doc_type,
            file_name=item.file_name,
            file_path=None,
            mime_type="application/pdf",
            upload_status="uploaded",
            ocr_status="running",
            parse_status="pending",
            page_count=None,
        )
        for item in payload.submitted_documents
    ]
    document_name_by_type = {document.doc_type: document.file_name for document in documents}
    return PackageDetailResponse(
        package_id=package_id,
        vendor_id=vendor_id,
        vendor_name=payload.vendor_name,
        package_status="processing",
        submitted_at=datetime.now(timezone.utc),
        assigned_reviewer=payload.assigned_reviewer,
        system_recommendation=None,
        final_decision=None,
        priority_score=40 + max(0, (3 - len(submitted_doc_types)) * 10),
        notes="New packet created from the intake form and queued for processing.",
        requirements=[
            DocumentRequirementSummary(
                required_doc_type=doc_type,
                is_required=True,
                is_satisfied=doc_type in submitted_doc_types,
                missing_reason=None
                if doc_type in submitted_doc_types
                else "Vendor has not submitted this required document yet.",
            )
            for doc_type in REQUIRED_DOC_TYPES
        ],
        documents=documents,
        extracted_fields=[],
        findings=[],
        evidence=[],
        review_history=[],
        processing_runs=[
            ProcessingRunSummary(
                processing_run_id=f"run_{uuid4().hex[:10]}",
                run_type="ingestion",
                run_status="completed",
                document_id=None,
                document_name=None,
                model_name=None,
                prompt_version=None,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                error_message=None,
            ),
            *[
                ProcessingRunSummary(
                    processing_run_id=f"run_{uuid4().hex[:10]}",
                    run_type="ocr",
                    run_status="running",
                    document_id=document.document_id,
                    document_name=document_name_by_type.get(document.doc_type),
                    model_name="azure-document-intelligence",
                    prompt_version=None,
                    started_at=datetime.now(timezone.utc),
                    completed_at=None,
                    error_message=None,
                )
                for document in documents
            ],
        ],
    )


def _complete_processing_runs(
    db: Session,
    package_id: str,
    documents: list[Document],
    ocr_required_document_ids: set[str] | None = None,
    ocr_completed_document_ids: set[str] | None = None,
) -> str | None:
    ocr_required_document_ids = ocr_required_document_ids or set()
    ocr_completed_document_ids = ocr_completed_document_ids or set()
    runs = db.scalars(
        select(ProcessingRun)
        .where(ProcessingRun.package_id == package_id)
        .order_by(ProcessingRun.started_at.asc())
    ).all()
    for run in runs:
        if run.run_type == "ocr" and run.document_id in ocr_required_document_ids:
            run.run_status = "needs_configuration"
            run.completed_at = datetime.now(timezone.utc)
            run.error_message = "No OCR engine is configured for scanned PDFs in local development."
            continue
        if run.run_type == "ocr" and run.document_id in ocr_completed_document_ids:
            run.run_status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            run.model_name = "azure-ai-documentintelligence"
            run.error_message = None
            continue
        if run.run_status in {"queued", "running"}:
            run.run_status = "completed"
            run.completed_at = datetime.now(timezone.utc)

    has_extraction_run = any(run.run_type == "field_extraction" for run in runs)
    has_validation_run = any(run.run_type == "policy_validation" for run in runs)
    extraction_run_id: str | None = next(
        (run.processing_run_id for run in runs if run.run_type == "field_extraction"),
        None,
    )

    if documents and not has_extraction_run:
        extraction_run = ProcessingRun(
            processing_run_id=f"run_{uuid4().hex[:10]}",
            package_id=package_id,
            document_id=documents[0].document_id,
            run_type="field_extraction",
            run_status="completed",
            model_name="gpt-4.1-mini",
            prompt_version="extract-v1",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        db.add(extraction_run)
        extraction_run_id = extraction_run.processing_run_id
    if not has_validation_run:
        db.add(
            ProcessingRun(
                processing_run_id=f"run_{uuid4().hex[:10]}",
                package_id=package_id,
                document_id=None,
                run_type="policy_validation",
                run_status="completed",
                model_name="rules-engine",
                prompt_version="policy-v1",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
        )
    return extraction_run_id


def _build_processing_findings(
    package: DocumentPackage,
    documents: list[Document],
    requirements: list[DocumentRequirement],
    extracted_fields: list[ExtractedField],
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    package_id = package.package_id
    missing_requirements = [
        requirement for requirement in requirements if requirement.is_required and not requirement.is_satisfied
    ]
    for requirement in missing_requirements:
        findings.append(
            ValidationFinding(
                finding_id=f"finding_{uuid4().hex[:12]}",
                package_id=package_id,
                document_id=None,
                finding_type="missing_document",
                severity="high",
                title=f"Missing required {requirement.required_doc_type.replace('_', ' ')}",
                description=(
                    f"The vendor packet is missing the required "
                    f"{requirement.required_doc_type.replace('_', ' ')} document."
                ),
                suggested_action="Request the missing document before final approval.",
                requires_human_review=True,
            )
        )

    for document in documents:
        if document.ocr_status == "required":
            findings.append(
                ValidationFinding(
                    finding_id=f"finding_{uuid4().hex[:12]}",
                    package_id=package_id,
                    document_id=document.document_id,
                    finding_type="data_gap",
                    severity="medium",
                    title=f"OCR required for uploaded {document.doc_type.replace('_', ' ')}",
                    description=(
                        "This PDF has no extractable text layer. Local development does not "
                        "currently have an OCR engine configured for scanned documents."
                    ),
                    suggested_action="Manually review the PDF or configure an OCR provider before approval.",
                    requires_human_review=True,
                )
            )

    contract = next((document for document in documents if document.doc_type == "contract"), None)
    w9 = next((document for document in documents if document.doc_type == "w9"), None)
    contract_name = next(
        (
            field
            for field in extracted_fields
            if field.field_name == "vendor_legal_name"
            and contract is not None
            and field.document_id == contract.document_id
        ),
        None,
    )
    w9_name = next(
        (
            field
            for field in extracted_fields
            if field.field_name == "vendor_legal_name"
            and w9 is not None
            and field.document_id == w9.document_id
        ),
        None,
    )
    tax_id_field = next(
        (field for field in extracted_fields if field.field_name == "tax_id"),
        None,
    )

    for document in (contract, w9):
        if (
            document is not None
            and _is_uploaded_pdf(document)
            and document.ocr_status != "required"
            and not any(
                field.field_name == "vendor_legal_name"
                and field.document_id == document.document_id
                for field in extracted_fields
            )
        ):
            findings.append(
                ValidationFinding(
                    finding_id=f"finding_{uuid4().hex[:12]}",
                    package_id=package_id,
                    document_id=document.document_id,
                    finding_type="data_gap",
                    severity="medium",
                    title=(
                        "Vendor legal name could not be extracted from uploaded "
                        f"{document.doc_type.replace('_', ' ')}"
                    ),
                    description=(
                        "No labelled vendor legal name was found in the text layer of "
                        "this PDF. It may be scanned, formatted differently, or incomplete."
                    ),
                    suggested_action="Verify the source document manually or request a clearer PDF.",
                    requires_human_review=True,
                )
            )

    if (
        w9 is not None
        and _is_uploaded_pdf(w9)
        and w9.ocr_status != "required"
        and tax_id_field is None
    ):
        findings.append(
            ValidationFinding(
                finding_id=f"finding_{uuid4().hex[:12]}",
                package_id=package_id,
                document_id=w9.document_id,
                finding_type="data_gap",
                severity="medium",
                title="Tax ID could not be extracted from uploaded W-9",
                description=(
                    "No U.S. EIN or SSN pattern was found in the text layer of the uploaded W-9."
                ),
                suggested_action="Verify the source document manually or request a clearer W-9.",
                requires_human_review=True,
            )
        )

    if contract_name and w9_name and _normalized_text(contract_name.raw_value) != _normalized_text(w9_name.raw_value):
        findings.append(
            ValidationFinding(
                finding_id=f"finding_{uuid4().hex[:12]}",
                package_id=package_id,
                document_id=contract.document_id if contract else None,
                finding_type="cross_document_mismatch",
                severity="medium",
                title="Vendor legal name differs between contract and W-9",
                description=(
                    f"The contract reads '{contract_name.raw_value}' while the W-9 "
                    f"reads '{w9_name.raw_value}'."
                ),
                suggested_action="Confirm both documents refer to the same legal entity before approval.",
                requires_human_review=True,
            )
        )

    if tax_id_field and (tax_id_field.raw_value is None or "Pending" in tax_id_field.raw_value):
        findings.append(
            ValidationFinding(
                finding_id=f"finding_{uuid4().hex[:12]}",
                package_id=package_id,
                document_id=tax_id_field.document_id,
                finding_type="data_gap",
                severity="medium",
                title="Tax ID could not be confidently verified",
                description="The extracted W-9 data does not contain a clean tax identification number.",
                suggested_action="Request a clearer W-9 or manually verify the tax ID before approval.",
                requires_human_review=True,
            )
        )

    if (
        package.vendor.category in {"software", "it_services"}
        and not any(
            finding.finding_type == "missing_document"
            and "insurance" in finding.title.lower()
            for finding in findings
        )
        and not any(document.doc_type == "insurance_certificate" for document in documents)
    ):
        findings.append(
            ValidationFinding(
                finding_id=f"finding_{uuid4().hex[:12]}",
                package_id=package_id,
                document_id=None,
                finding_type="policy_violation",
                severity="high",
                title="Insurance document required for software vendors",
                description=(
                    "The vendor is categorized as software/IT services, but an insurance "
                    "certificate was not included for automated validation."
                ),
                suggested_action="Request the certificate of insurance before approval.",
                requires_human_review=True,
            )
        )

    if not missing_requirements and documents and len(findings) == 0:
        if contract is not None:
            findings.append(
                ValidationFinding(
                    finding_id=f"finding_{uuid4().hex[:12]}",
                    package_id=package_id,
                    document_id=contract.document_id,
                    finding_type="confidence_check",
                    severity="low",
                    title="New packet requires final reviewer spot-check",
                    description=(
                        "Automated processing completed successfully, but procurement should "
                        "confirm the contract and vendor profile before approval."
                    ),
                    suggested_action="Quickly confirm the key extracted values and approve if acceptable.",
                    requires_human_review=True,
                )
            )

    return findings


def _build_sample_processing_findings(
    package_id: str,
    vendor_name: str,
    documents: list[DocumentSummary],
    requirements: list[DocumentRequirementSummary],
    extracted_fields: list[ExtractedFieldSummary],
) -> list[FindingSummary]:
    findings: list[FindingSummary] = []
    missing_requirements = [
        requirement for requirement in requirements if requirement.is_required and not requirement.is_satisfied
    ]
    for requirement in missing_requirements:
        findings.append(
            FindingSummary(
                finding_id=f"finding_{uuid4().hex[:12]}",
                finding_type="missing_document",
                severity="high",
                title=f"Missing required {requirement.required_doc_type.replace('_', ' ')}",
                description=(
                    f"The vendor packet is missing the required "
                    f"{requirement.required_doc_type.replace('_', ' ')} document."
                ),
                suggested_action="Request the missing document before final approval.",
                requires_human_review=True,
            )
        )

    contract = next((document for document in documents if document.doc_type == "contract"), None)
    w9 = next((document for document in documents if document.doc_type == "w9"), None)
    contract_name = next(
        (
            field
            for field in extracted_fields
            if field.field_name == "vendor_legal_name"
            and contract is not None
            and field.source_document_id == contract.document_id
        ),
        None,
    )
    w9_name = next(
        (
            field
            for field in extracted_fields
            if field.field_name == "vendor_legal_name"
            and w9 is not None
            and field.source_document_id == w9.document_id
        ),
        None,
    )
    tax_id_field = next(
        (field for field in extracted_fields if field.field_name == "tax_id"),
        None,
    )

    if contract_name and w9_name and _normalized_text(contract_name.raw_value) != _normalized_text(w9_name.raw_value):
        findings.append(
            FindingSummary(
                finding_id=f"finding_{uuid4().hex[:12]}",
                finding_type="cross_document_mismatch",
                severity="medium",
                title="Vendor legal name differs between contract and W-9",
                description=(
                    f"The contract reads '{contract_name.raw_value}' while the W-9 "
                    f"reads '{w9_name.raw_value}'."
                ),
                suggested_action="Confirm both documents refer to the same legal entity before approval.",
                requires_human_review=True,
            )
        )

    if tax_id_field and (tax_id_field.raw_value is None or "Pending" in tax_id_field.raw_value):
        findings.append(
            FindingSummary(
                finding_id=f"finding_{uuid4().hex[:12]}",
                finding_type="data_gap",
                severity="medium",
                title="Tax ID could not be confidently verified",
                description="The extracted W-9 data does not contain a clean tax identification number.",
                suggested_action="Request a clearer W-9 or manually verify the tax ID before approval.",
                requires_human_review=True,
            )
        )

    if not missing_requirements and documents and len(findings) == 0:
        findings.append(
            FindingSummary(
                finding_id=f"finding_{uuid4().hex[:12]}",
                finding_type="confidence_check",
                severity="low",
                title="New packet requires final reviewer spot-check",
                description=(
                    "Automated processing completed successfully, but procurement should "
                    "confirm the contract and vendor profile before approval."
                ),
                suggested_action="Quickly confirm the key extracted values and approve if acceptable.",
                requires_human_review=True,
            )
        )
    return findings


def _build_processing_fields(
    package: DocumentPackage,
    documents: list[Document],
    extraction_run_id: str | None,
    text_extractions: dict[str, DocumentTextExtraction | None] | None = None,
) -> tuple[list[ExtractedField], list[FieldNormalization]]:
    extracted_fields: list[ExtractedField] = []
    normalizations: list[FieldNormalization] = []

    for document in documents:
        text_extraction = (
            text_extractions.get(document.document_id)
            if text_extractions is not None
            else _extract_uploaded_pdf_text(document)
        )
        if text_extraction is not None:
            fields, field_normalizations = _build_uploaded_pdf_fields(
                document, text_extraction.pages, extraction_run_id
            )
            extracted_fields.extend(fields)
            normalizations.extend(field_normalizations)
            continue

        if document.doc_type == "contract":
            contract_name_value = _contract_vendor_name_variant(package.vendor.legal_name)
            field = ExtractedField(
                field_id=f"field_{uuid4().hex[:12]}",
                document_id=document.document_id,
                processing_run_id=extraction_run_id,
                field_name="vendor_legal_name",
                raw_value=contract_name_value,
                value_type="string",
                confidence=Decimal("0.9700"),
                source_page=1,
                source_span_text=contract_name_value,
            )
            extracted_fields.append(field)
            normalizations.append(
                FieldNormalization(
                    normalization_id=f"norm_{uuid4().hex[:12]}",
                    field_id=field.field_id,
                    normalized_value=_normalized_text(contract_name_value),
                    normalization_method="string_normalization",
                    normalization_confidence=Decimal("0.9900"),
                )
            )
            terms = ExtractedField(
                field_id=f"field_{uuid4().hex[:12]}",
                document_id=document.document_id,
                processing_run_id=extraction_run_id,
                field_name="payment_terms",
                raw_value="Net 30",
                value_type="integer",
                confidence=Decimal("0.9300"),
                source_page=1,
                source_span_text="Net 30",
            )
            extracted_fields.append(terms)
            normalizations.append(
                FieldNormalization(
                    normalization_id=f"norm_{uuid4().hex[:12]}",
                    field_id=terms.field_id,
                    normalized_value="30",
                    normalization_method="payment_terms_normalization",
                    normalization_confidence=Decimal("0.9600"),
                )
            )
        elif document.doc_type == "w9":
            tax_value = package.vendor.tax_id or "Pending vendor tax ID"
            name_field = ExtractedField(
                field_id=f"field_{uuid4().hex[:12]}",
                document_id=document.document_id,
                processing_run_id=extraction_run_id,
                field_name="vendor_legal_name",
                raw_value=package.vendor.legal_name,
                value_type="string",
                confidence=Decimal("0.9850"),
                source_page=1,
                source_span_text=package.vendor.legal_name,
            )
            tax_field = ExtractedField(
                field_id=f"field_{uuid4().hex[:12]}",
                document_id=document.document_id,
                processing_run_id=extraction_run_id,
                field_name="tax_id",
                raw_value=tax_value,
                value_type="tax_id",
                confidence=Decimal("0.9920") if package.vendor.tax_id else Decimal("0.7500"),
                source_page=1,
                source_span_text=tax_value,
            )
            extracted_fields.extend([name_field, tax_field])
            normalizations.extend(
                [
                    FieldNormalization(
                        normalization_id=f"norm_{uuid4().hex[:12]}",
                        field_id=name_field.field_id,
                        normalized_value=package.vendor.legal_name.lower(),
                        normalization_method="string_normalization",
                        normalization_confidence=Decimal("0.9900"),
                    ),
                    FieldNormalization(
                        normalization_id=f"norm_{uuid4().hex[:12]}",
                        field_id=tax_field.field_id,
                        normalized_value=(package.vendor.tax_id or "").replace("-", "") or None,
                        normalization_method="tax_id_cleanup",
                        normalization_confidence=Decimal("0.9800") if package.vendor.tax_id else Decimal("0.7000"),
                    ),
                ]
            )
        elif document.doc_type == "insurance_certificate":
            coverage = ExtractedField(
                field_id=f"field_{uuid4().hex[:12]}",
                document_id=document.document_id,
                processing_run_id=extraction_run_id,
                field_name="insurance_coverage",
                raw_value="$1,000,000",
                value_type="currency",
                confidence=Decimal("0.9550"),
                source_page=1,
                source_span_text="$1,000,000",
            )
            extracted_fields.append(coverage)
            normalizations.append(
                FieldNormalization(
                    normalization_id=f"norm_{uuid4().hex[:12]}",
                    field_id=coverage.field_id,
                    normalized_value="1000000",
                    normalization_method="currency_normalization",
                    normalization_confidence=Decimal("0.9800"),
                )
            )

    return extracted_fields, normalizations


def _extract_uploaded_pdf_text(document: Document) -> DocumentTextExtraction | None:
    """Use the PDF text layer first, then Azure OCR when configured."""
    if not _is_uploaded_pdf(document):
        return None
    storage_key = document.storage_key or legacy_local_document_key(
        document.package_id, document.document_id, document.file_name
    )
    try:
        contents = get_document_storage().read_bytes(storage_key)
    except (FileNotFoundError, OSError):
        return DocumentTextExtraction([], "file_unavailable", "Uploaded PDF file is unavailable.")
    try:
        reader = PdfReader(BytesIO(contents))
        pages = [
            (page_number, page.extract_text() or "")
            for page_number, page in enumerate(reader.pages, start=1)
        ]
    except Exception:
        return DocumentTextExtraction([], "pdf_read_error", "Uploaded PDF could not be read.")

    if any(text.strip() for _page_number, text in pages):
        return DocumentTextExtraction(pages, "pdf_text_layer")
    return _extract_with_azure_document_intelligence(contents)


def _extract_with_azure_document_intelligence(contents: bytes) -> DocumentTextExtraction:
    """Run Azure Read OCR only when credentials are explicitly configured."""
    endpoint = settings.document_intelligence_endpoint
    api_key = settings.document_intelligence_api_key
    if not endpoint or not api_key:
        return DocumentTextExtraction(
            [],
            "ocr_unconfigured",
            "Azure AI Document Intelligence endpoint and API key are not configured.",
        )

    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential

        client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )
        result = client.begin_analyze_document("prebuilt-read", body=BytesIO(contents)).result()
        pages = [
            (
                page_number,
                "\n".join(line.content for line in page.lines or []),
            )
            for page_number, page in enumerate(result.pages or [], start=1)
        ]
        text_pages = [item for item in pages if item[1].strip()]
        if text_pages:
            return DocumentTextExtraction(text_pages, "azure_ai_document_intelligence")
        return DocumentTextExtraction([], "azure_ai_document_intelligence", "Azure OCR returned no text.")
    except Exception as exc:
        return DocumentTextExtraction(
            [],
            "azure_ai_document_intelligence",
            f"Azure OCR request failed: {type(exc).__name__}.",
        )


def _is_uploaded_pdf(document: Document) -> bool:
    return bool(document.file_path and document.file_path.startswith("/api/packages/"))


def _build_uploaded_pdf_fields(
    document: Document,
    pages: list[tuple[int, str]],
    extraction_run_id: str | None,
) -> tuple[list[ExtractedField], list[FieldNormalization]]:
    """Extract only deterministic, reviewable values from text-based PDFs."""
    fields: list[ExtractedField] = []
    normalizations: list[FieldNormalization] = []

    def add_field(
        field_name: str,
        raw_value: str,
        value_type: str,
        page_number: int,
        normalized_value: str | None,
        normalization_method: str,
    ) -> None:
        field = ExtractedField(
            field_id=f"field_{uuid4().hex[:12]}",
            document_id=document.document_id,
            processing_run_id=extraction_run_id,
            field_name=field_name,
            raw_value=raw_value,
            value_type=value_type,
            confidence=Decimal("0.8600"),
            source_page=page_number,
            source_span_text=raw_value,
        )
        fields.append(field)
        normalizations.append(
            FieldNormalization(
                normalization_id=f"norm_{uuid4().hex[:12]}",
                field_id=field.field_id,
                normalized_value=normalized_value,
                normalization_method=normalization_method,
                normalization_confidence=Decimal("0.9000"),
            )
        )

    name_patterns = {
        "contract": [
            r"(?:vendor legal name|vendor|supplier|service provider)\s*[:\-]\s*"
            r"([^\n\r]{2,120}?)(?=\s*(?:payment terms|tax id|ein)\s*[:\-]|$)",
        ],
        "w9": [
            r"(?:vendor legal name|legal name|business name|name)\s*[:\-]\s*"
            r"([^\n\r]{2,120}?)(?=\s*(?:ein|tax id|ssn)\s*[:\-]|$)",
        ],
    }
    if document.doc_type in name_patterns:
        name = _find_pdf_value(pages, name_patterns[document.doc_type])
        if name is not None:
            value, page_number = name
            add_field(
                "vendor_legal_name",
                value,
                "string",
                page_number,
                _normalized_text(value),
                "string_normalization",
            )

    if document.doc_type == "contract":
        terms = _find_pdf_value(pages, [r"\b(net\s*\d{1,3})\b"])
        if terms is not None:
            value, page_number = terms
            days_match = re.search(r"\d+", value)
            add_field(
                "payment_terms",
                value.title(),
                "string",
                page_number,
                days_match.group(0) if days_match else None,
                "payment_terms_normalization",
            )

    if document.doc_type == "w9":
        tax_id = _find_pdf_value(pages, [r"\b(?:\d{2}-?\d{7}|\d{3}-?\d{2}-?\d{4})\b"])
        if tax_id is not None:
            value, page_number = tax_id
            add_field(
                "tax_id",
                value,
                "tax_id",
                page_number,
                value.replace("-", ""),
                "tax_id_cleanup",
            )
        address = _find_pdf_value(
            pages,
            [
                r"(?:business\s+)?address\s*[:\-]\s*"
                r"([^\n\r]{3,120}(?:\s*[\n\r]+[^\n\r]{3,120}){0,2})"
            ],
        )
        if address is not None:
            value, page_number = address
            add_field(
                "vendor_address",
                value,
                "address",
                page_number,
                _normalized_text(value),
                "address_whitespace_normalization",
            )

    if document.doc_type == "insurance_certificate":
        coverage = _find_pdf_value(
            pages,
            [r"(?:each occurrence|general aggregate|coverage|limit)\D{0,40}(\$[\d,]+(?:\.\d{2})?)"],
        )
        if coverage is not None:
            value, page_number = coverage
            add_field(
                "insurance_coverage",
                value,
                "currency",
                page_number,
                re.sub(r"[^0-9]", "", value),
                "currency_normalization",
            )

    return fields, normalizations


def _find_pdf_value(
    pages: list[tuple[int, str]], patterns: list[str]
) -> tuple[str, int] | None:
    for page_number, text in pages:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                matched_value = match.group(1) if match.lastindex else match.group(0)
                value = " ".join(matched_value.strip().split())
                if value:
                    return value, page_number
    return None


def _build_processing_evidence(
    findings: list[ValidationFinding],
    extracted_fields: list[ExtractedField],
    documents: list[Document],
) -> list[DecisionEvidence]:
    fields_by_name: dict[str, list[ExtractedField]] = {}
    for field in extracted_fields:
        fields_by_name.setdefault(field.field_name, []).append(field)
    document_by_id = {document.document_id: document for document in documents}
    evidence: list[DecisionEvidence] = []

    for finding in findings:
        if finding.finding_type == "missing_document":
            evidence.append(
                DecisionEvidence(
                    evidence_id=f"ev_{uuid4().hex[:12]}",
                    package_id=finding.package_id,
                    finding_id=finding.finding_id,
                    field_id=None,
                    document_id=None,
                    evidence_type="status_note",
                    page_num=None,
                    snippet_text="Required document has not yet been submitted in the intake packet.",
                )
            )
            continue

        if finding.finding_type == "cross_document_mismatch":
            for field in fields_by_name.get("vendor_legal_name", [])[:2]:
                document = document_by_id.get(field.document_id)
                evidence.append(
                    DecisionEvidence(
                        evidence_id=f"ev_{uuid4().hex[:12]}",
                        package_id=finding.package_id,
                        finding_id=finding.finding_id,
                        field_id=field.field_id,
                        document_id=field.document_id,
                        evidence_type="snippet",
                        page_num=field.source_page,
                        snippet_text=field.source_span_text
                        or (document.file_name if document else "Vendor name snippet"),
                    )
                )
            continue

        if finding.finding_type == "data_gap":
            tax_field = next(iter(fields_by_name.get("tax_id", [])), None)
            evidence.append(
                DecisionEvidence(
                    evidence_id=f"ev_{uuid4().hex[:12]}",
                    package_id=finding.package_id,
                    finding_id=finding.finding_id,
                    field_id=tax_field.field_id if tax_field else None,
                    document_id=tax_field.document_id if tax_field else None,
                    evidence_type="snippet",
                    page_num=tax_field.source_page if tax_field else 1,
                    snippet_text=tax_field.source_span_text if tax_field else "Pending vendor tax ID",
                )
            )
            continue

        contract_document = next(
            (document for document in documents if document.doc_type == "contract"),
            None,
        )
        if contract_document is not None:
            vendor_name_field = next(iter(fields_by_name.get("vendor_legal_name", [])), None)
            payment_terms_field = next(iter(fields_by_name.get("payment_terms", [])), None)
            selected_field = payment_terms_field or vendor_name_field
            snippet_text = (
                payment_terms_field.source_span_text
                if payment_terms_field and payment_terms_field.source_span_text
                else f"Contract review spot-check for {document_by_id[contract_document.document_id].file_name}"
            )
            evidence.append(
                DecisionEvidence(
                    evidence_id=f"ev_{uuid4().hex[:12]}",
                    package_id=finding.package_id,
                    finding_id=finding.finding_id,
                    field_id=selected_field.field_id if selected_field else None,
                    document_id=contract_document.document_id,
                    evidence_type="snippet",
                    page_num=1,
                    snippet_text=snippet_text,
                )
            )

    return evidence


def _build_sample_processing_fields(
    vendor_name: str,
    documents: list[DocumentSummary],
) -> list[ExtractedFieldSummary]:
    fields: list[ExtractedFieldSummary] = []
    for document in documents:
        if document.doc_type == "contract":
            contract_name_value = _contract_vendor_name_variant(vendor_name)
            fields.extend(
                [
                    ExtractedFieldSummary(
                        field_name="vendor_legal_name",
                        raw_value=contract_name_value,
                        normalized_value=_normalized_text(contract_name_value),
                        confidence=0.97,
                        source_document_id=document.document_id,
                        source_page=1,
                    ),
                    ExtractedFieldSummary(
                        field_name="payment_terms",
                        raw_value="Net 30",
                        normalized_value="30",
                        confidence=0.93,
                        source_document_id=document.document_id,
                        source_page=1,
                    ),
                ]
            )
        elif document.doc_type == "w9":
            fields.extend(
                [
                    ExtractedFieldSummary(
                        field_name="vendor_legal_name",
                        raw_value=vendor_name,
                        normalized_value=vendor_name.lower(),
                        confidence=0.985,
                        source_document_id=document.document_id,
                        source_page=1,
                    ),
                    ExtractedFieldSummary(
                        field_name="tax_id",
                        raw_value="Pending vendor tax ID",
                        normalized_value=None,
                        confidence=0.75,
                        source_document_id=document.document_id,
                        source_page=1,
                    ),
                ]
            )
        elif document.doc_type == "insurance_certificate":
            fields.append(
                ExtractedFieldSummary(
                    field_name="insurance_coverage",
                    raw_value="$1,000,000",
                    normalized_value="1000000",
                    confidence=0.955,
                    source_document_id=document.document_id,
                    source_page=1,
                )
            )
    return fields


def _build_sample_processing_evidence(
    findings: list[FindingSummary],
    extracted_fields: list[ExtractedFieldSummary],
    documents: list[DocumentSummary],
) -> list[EvidenceSummary]:
    evidence: list[EvidenceSummary] = []
    contract_document = next((document for document in documents if document.doc_type == "contract"), None)
    payment_terms_field = next(
        (field for field in extracted_fields if field.field_name == "payment_terms"),
        None,
    )

    for finding in findings:
        if finding.finding_type == "missing_document":
            evidence.append(
                EvidenceSummary(
                    evidence_id=f"ev_{uuid4().hex[:12]}",
                    evidence_type="status_note",
                    document_id="",
                    document_name="Submission checklist",
                    page_num=None,
                    snippet_text="Required document has not yet been submitted in the intake packet.",
                    related_finding_id=finding.finding_id,
                )
            )
        elif finding.finding_type == "cross_document_mismatch":
            for field in [
                field for field in extracted_fields if field.field_name == "vendor_legal_name"
            ][:2]:
                document = next(
                    (
                        item
                        for item in documents
                        if item.document_id == field.source_document_id
                    ),
                    None,
                )
                evidence.append(
                    EvidenceSummary(
                        evidence_id=f"ev_{uuid4().hex[:12]}",
                        evidence_type="snippet",
                        document_id=field.source_document_id,
                        document_name=document.file_name if document else "Vendor document",
                        page_num=field.source_page,
                        snippet_text=field.raw_value,
                        related_finding_id=finding.finding_id,
                    )
                )
            continue
        elif finding.finding_type == "data_gap":
            tax_field = next(
                (field for field in extracted_fields if field.field_name == "tax_id"),
                None,
            )
            evidence.append(
                EvidenceSummary(
                    evidence_id=f"ev_{uuid4().hex[:12]}",
                    evidence_type="snippet",
                    document_id=tax_field.source_document_id if tax_field else "",
                    document_name=next(
                        (
                            item.file_name
                            for item in documents
                            if tax_field and item.document_id == tax_field.source_document_id
                        ),
                        "W-9",
                    ),
                    page_num=tax_field.source_page if tax_field else 1,
                    snippet_text=tax_field.raw_value if tax_field else "Pending vendor tax ID",
                    related_finding_id=finding.finding_id,
                )
            )
            continue
        elif contract_document is not None:
            evidence.append(
                EvidenceSummary(
                    evidence_id=f"ev_{uuid4().hex[:12]}",
                    evidence_type="snippet",
                    document_id=contract_document.document_id,
                    document_name=contract_document.file_name,
                    page_num=1,
                    snippet_text=payment_terms_field.raw_value if payment_terms_field else "Contract requires a quick reviewer spot-check.",
                    related_finding_id=finding.finding_id,
                )
            )
    return evidence


def _contract_vendor_name_variant(vendor_name: str) -> str:
    if "LLC" in vendor_name and len(vendor_name.split()) >= 2:
        return vendor_name.replace(" LLC", " Group LLC")
    if "Inc." in vendor_name:
        return vendor_name.replace(" Inc.", " Incorporated")
    if "Ltd" in vendor_name:
        return vendor_name.replace(" Ltd", " Limited")
    return vendor_name


def _normalized_text(value: str | None) -> str:
    if not value:
        return ""
    return (
        value.lower()
        .replace(" incorporated", " inc")
        .replace(" limited", " ltd")
        .replace(" group", "")
        .replace(".", "")
        .replace(",", "")
        .replace("  ", " ")
        .strip()
    )
