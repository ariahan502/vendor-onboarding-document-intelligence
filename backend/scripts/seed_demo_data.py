from datetime import datetime

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.decisioning import DecisionEvidence, ReviewDecision, ValidationFinding
from app.models.documents import Document, DocumentPackage, DocumentRequirement, Vendor
from app.models.processing import ExtractedField, FieldNormalization, ProcessingRun


def main() -> None:
    db = SessionLocal()
    try:
        _clear_existing_demo_data(db)

        vendor_1 = Vendor(
            vendor_id="ven_abc_consulting",
            legal_name="ABC Consulting LLC",
            normalized_legal_name="abc consulting",
            tax_id="12-3456789",
            country="US",
            category="consulting",
        )
        vendor_2 = Vendor(
            vendor_id="ven_blue_peak",
            legal_name="Blue Peak Analytics Inc.",
            normalized_legal_name="blue peak analytics",
            tax_id="98-7654321",
            country="US",
            category="software",
        )

        package_1 = DocumentPackage(
            package_id="pkg_1001",
            vendor_id=vendor_1.vendor_id,
            package_status="ready_for_review",
            submitted_at=datetime.fromisoformat("2026-07-28T10:15:00"),
            assigned_reviewer="aria.han",
            system_recommendation="needs_review",
            final_decision=None,
            priority_score=82,
            notes="Insurance and naming issues need reviewer confirmation.",
        )
        package_2 = DocumentPackage(
            package_id="pkg_1002",
            vendor_id=vendor_2.vendor_id,
            package_status="processing",
            submitted_at=datetime.fromisoformat("2026-07-29T09:00:00"),
            assigned_reviewer=None,
            system_recommendation=None,
            final_decision=None,
            priority_score=35,
            notes=None,
        )

        db.add_all([vendor_1, vendor_2, package_1, package_2])

        db.add_all(
            [
                DocumentRequirement(
                    requirement_id="req_contract_1001",
                    package_id=package_1.package_id,
                    required_doc_type="contract",
                    is_required=True,
                    is_satisfied=True,
                ),
                DocumentRequirement(
                    requirement_id="req_w9_1001",
                    package_id=package_1.package_id,
                    required_doc_type="w9",
                    is_required=True,
                    is_satisfied=True,
                ),
                DocumentRequirement(
                    requirement_id="req_insurance_1001",
                    package_id=package_1.package_id,
                    required_doc_type="insurance_certificate",
                    is_required=True,
                    is_satisfied=True,
                ),
                DocumentRequirement(
                    requirement_id="req_vendor_form_1001",
                    package_id=package_1.package_id,
                    required_doc_type="vendor_registration_form",
                    is_required=False,
                    is_satisfied=False,
                    missing_reason="Optional in MVP workflow.",
                ),
            ]
        )

        db.add_all(
            [
                Document(
                    document_id="doc_contract_001",
                    package_id=package_1.package_id,
                    doc_type="contract",
                    file_name="ABC_Master_Services_Agreement.pdf",
                    file_path="/sample-documents/ABC_Master_Services_Agreement.pdf",
                    mime_type="application/pdf",
                    page_count=1,
                    upload_status="uploaded",
                    ocr_status="completed",
                    parse_status="completed",
                    uploaded_at=datetime.fromisoformat("2026-07-28T10:16:00"),
                ),
                Document(
                    document_id="doc_w9_001",
                    package_id=package_1.package_id,
                    doc_type="w9",
                    file_name="ABC_W9.pdf",
                    file_path="/sample-documents/ABC_W9.pdf",
                    mime_type="application/pdf",
                    page_count=1,
                    upload_status="uploaded",
                    ocr_status="completed",
                    parse_status="completed",
                    uploaded_at=datetime.fromisoformat("2026-07-28T10:16:30"),
                ),
                Document(
                    document_id="doc_insurance_001",
                    package_id=package_1.package_id,
                    doc_type="insurance_certificate",
                    file_name="ABC_Insurance_Certificate.pdf",
                    file_path="/sample-documents/ABC_Insurance_Certificate.pdf",
                    mime_type="application/pdf",
                    page_count=1,
                    upload_status="uploaded",
                    ocr_status="completed",
                    parse_status="completed",
                    uploaded_at=datetime.fromisoformat("2026-07-28T10:17:00"),
                ),
            ]
        )

        db.add_all(
            [
                ProcessingRun(
                    processing_run_id="run_pkg_1001_ingest",
                    package_id=package_1.package_id,
                    document_id=None,
                    run_type="ingestion",
                    run_status="completed",
                    started_at=datetime.fromisoformat("2026-07-28T10:15:20"),
                    completed_at=datetime.fromisoformat("2026-07-28T10:15:45"),
                ),
                ProcessingRun(
                    processing_run_id="run_doc_contract_ocr",
                    package_id=package_1.package_id,
                    document_id="doc_contract_001",
                    run_type="ocr",
                    run_status="completed",
                    model_name="azure-document-intelligence",
                    started_at=datetime.fromisoformat("2026-07-28T10:16:05"),
                    completed_at=datetime.fromisoformat("2026-07-28T10:16:40"),
                ),
                ProcessingRun(
                    processing_run_id="run_doc_w9_extract",
                    package_id=package_1.package_id,
                    document_id="doc_w9_001",
                    run_type="field_extraction",
                    run_status="completed",
                    model_name="gpt-4.1-mini",
                    prompt_version="extract-v1",
                    started_at=datetime.fromisoformat("2026-07-28T10:17:10"),
                    completed_at=datetime.fromisoformat("2026-07-28T10:17:45"),
                ),
                ProcessingRun(
                    processing_run_id="run_pkg_1001_policy",
                    package_id=package_1.package_id,
                    document_id=None,
                    run_type="policy_validation",
                    run_status="completed",
                    model_name="rules-engine",
                    prompt_version="policy-v1",
                    started_at=datetime.fromisoformat("2026-07-28T10:18:00"),
                    completed_at=datetime.fromisoformat("2026-07-28T10:18:12"),
                ),
                ProcessingRun(
                    processing_run_id="run_pkg_1002_ingest",
                    package_id=package_2.package_id,
                    document_id=None,
                    run_type="ingestion",
                    run_status="completed",
                    started_at=datetime.fromisoformat("2026-07-29T09:00:15"),
                    completed_at=datetime.fromisoformat("2026-07-29T09:00:40"),
                ),
                ProcessingRun(
                    processing_run_id="run_pkg_1002_ocr",
                    package_id=package_2.package_id,
                    document_id=None,
                    run_type="ocr",
                    run_status="running",
                    model_name="azure-document-intelligence",
                    started_at=datetime.fromisoformat("2026-07-29T09:01:00"),
                    completed_at=None,
                ),
            ]
        )

        db.add_all(
            [
                ExtractedField(
                    field_id="field_contract_name_001",
                    document_id="doc_contract_001",
                    field_name="vendor_legal_name",
                    raw_value="ABC Consulting Group LLC",
                    value_type="string",
                    confidence=0.97,
                    source_page=1,
                    source_span_text="ABC Consulting Group LLC",
                ),
                ExtractedField(
                    field_id="field_w9_name_001",
                    document_id="doc_w9_001",
                    field_name="vendor_legal_name",
                    raw_value="ABC Consulting LLC",
                    value_type="string",
                    confidence=0.99,
                    source_page=1,
                    source_span_text="ABC Consulting LLC",
                ),
                ExtractedField(
                    field_id="field_w9_tax_id_001",
                    document_id="doc_w9_001",
                    field_name="tax_id",
                    raw_value="12-3456789",
                    value_type="tax_id",
                    confidence=0.99,
                    source_page=1,
                    source_span_text="12-3456789",
                ),
                ExtractedField(
                    field_id="field_insurance_coverage_001",
                    document_id="doc_insurance_001",
                    field_name="insurance_coverage",
                    raw_value="$500,000",
                    value_type="currency",
                    confidence=0.96,
                    source_page=1,
                    source_span_text="$500,000",
                ),
                ExtractedField(
                    field_id="field_contract_terms_001",
                    document_id="doc_contract_001",
                    field_name="payment_terms",
                    raw_value="Net 60",
                    value_type="integer",
                    confidence=0.91,
                    source_page=1,
                    source_span_text="Net 60",
                ),
            ]
        )

        db.add_all(
            [
                FieldNormalization(
                    normalization_id="norm_contract_name_001",
                    field_id="field_contract_name_001",
                    normalized_value="abc consulting group",
                    normalization_method="string_normalization",
                    normalization_confidence=0.99,
                ),
                FieldNormalization(
                    normalization_id="norm_w9_name_001",
                    field_id="field_w9_name_001",
                    normalized_value="abc consulting",
                    normalization_method="string_normalization",
                    normalization_confidence=0.99,
                ),
                FieldNormalization(
                    normalization_id="norm_w9_tax_id_001",
                    field_id="field_w9_tax_id_001",
                    normalized_value="123456789",
                    normalization_method="tax_id_cleanup",
                    normalization_confidence=1.0,
                ),
                FieldNormalization(
                    normalization_id="norm_insurance_coverage_001",
                    field_id="field_insurance_coverage_001",
                    normalized_value="500000",
                    normalization_method="currency_normalization",
                    normalization_confidence=0.98,
                ),
                FieldNormalization(
                    normalization_id="norm_contract_terms_001",
                    field_id="field_contract_terms_001",
                    normalized_value="60",
                    normalization_method="payment_terms_normalization",
                    normalization_confidence=0.95,
                ),
            ]
        )

        db.add_all(
            [
                ValidationFinding(
                    finding_id="finding_name_mismatch_001",
                    package_id=package_1.package_id,
                    document_id="doc_contract_001",
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
                ValidationFinding(
                    finding_id="finding_insurance_coverage_001",
                    package_id=package_1.package_id,
                    document_id="doc_insurance_001",
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
                ValidationFinding(
                    finding_id="finding_payment_terms_001",
                    package_id=package_1.package_id,
                    document_id="doc_contract_001",
                    finding_type="policy_violation",
                    severity="medium",
                    title="Payment terms may exceed standard policy limit",
                    description="The contract appears to specify Net 60 terms.",
                    suggested_action="Confirm whether exception approval exists.",
                    requires_human_review=True,
                ),
            ]
        )

        db.add_all(
            [
                DecisionEvidence(
                    evidence_id="ev_001",
                    package_id=package_1.package_id,
                    finding_id="finding_name_mismatch_001",
                    field_id="field_contract_name_001",
                    document_id="doc_contract_001",
                    evidence_type="snippet",
                    page_num=1,
                    snippet_text="This Master Services Agreement is entered into by ABC Consulting Group LLC...",
                ),
                DecisionEvidence(
                    evidence_id="ev_002",
                    package_id=package_1.package_id,
                    finding_id="finding_name_mismatch_001",
                    field_id="field_w9_name_001",
                    document_id="doc_w9_001",
                    evidence_type="snippet",
                    page_num=1,
                    snippet_text="Business name: ABC Consulting LLC",
                ),
                DecisionEvidence(
                    evidence_id="ev_003",
                    package_id=package_1.package_id,
                    finding_id="finding_insurance_coverage_001",
                    field_id="field_insurance_coverage_001",
                    document_id="doc_insurance_001",
                    evidence_type="snippet",
                    page_num=1,
                    snippet_text="General Liability: $500,000",
                ),
            ]
        )

        db.add(
            ReviewDecision(
                decision_id="decision_prev_001",
                package_id=package_1.package_id,
                reviewer="system_seed",
                system_recommendation="needs_review",
                final_decision="needs_review",
                reviewer_comment="Seed case for MVP demo and early UI work.",
                decision_at=datetime.fromisoformat("2026-07-28T10:25:00"),
            )
        )

        db.commit()
        print("Seeded demo vendor onboarding data.")
    finally:
        db.close()


def _clear_existing_demo_data(db) -> None:
    ids = ["pkg_1001", "pkg_1002"]
    vendor_ids = ["ven_abc_consulting", "ven_blue_peak"]
    document_ids = ["doc_contract_001", "doc_w9_001", "doc_insurance_001"]
    processing_run_ids = [
        "run_pkg_1001_ingest",
        "run_doc_contract_ocr",
        "run_doc_w9_extract",
        "run_pkg_1001_policy",
        "run_pkg_1002_ingest",
        "run_pkg_1002_ocr",
    ]

    db.execute(delete(ReviewDecision).where(ReviewDecision.package_id.in_(ids)))
    db.execute(delete(DecisionEvidence).where(DecisionEvidence.package_id.in_(ids)))
    db.execute(delete(ValidationFinding).where(ValidationFinding.package_id.in_(ids)))
    db.execute(delete(FieldNormalization).where(FieldNormalization.field_id.in_([
        "field_contract_name_001",
        "field_w9_name_001",
        "field_w9_tax_id_001",
        "field_insurance_coverage_001",
        "field_contract_terms_001",
    ])))
    db.execute(
        delete(ProcessingRun).where(
            ProcessingRun.processing_run_id.in_(processing_run_ids)
        )
    )
    db.execute(delete(ExtractedField).where(ExtractedField.document_id.in_(document_ids)))
    db.execute(delete(Document).where(Document.document_id.in_(document_ids)))
    db.execute(delete(DocumentRequirement).where(DocumentRequirement.package_id.in_(ids)))
    db.execute(delete(DocumentPackage).where(DocumentPackage.package_id.in_(ids)))
    db.execute(delete(Vendor).where(Vendor.vendor_id.in_(vendor_ids)))
    db.commit()
