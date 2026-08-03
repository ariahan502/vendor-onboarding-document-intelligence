from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.auth import CurrentActor, require_roles
from app.schemas.packages import (
    PackageCreateRequest,
    PackageCreateResponse,
    PackageDetailResponse,
    DocumentUploadResponse,
    FieldReviewOverrideCreateRequest,
    FieldReviewOverrideCreateResponse,
    FindingResolutionCreateRequest,
    FindingResolutionCreateResponse,
    PackageQueueResponse,
    PackageSimulationResponse,
    ReviewDecisionCreateRequest,
    ReviewDecisionCreateResponse,
)
from app.services.package_service import (
    create_package,
    create_field_review_override,
    create_finding_resolution,
    create_review_decision,
    get_document_file,
    get_package_detail,
    list_package_queue,
    simulate_package_processing,
    upload_document_file,
)
from app.services.audit_service import record_audit_event

router = APIRouter()


@router.get("/", response_model=PackageQueueResponse)
def list_packages(
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_roles("intake", "reviewer", "admin")),
) -> PackageQueueResponse:
    """Return queue data for the reviewer worklist."""
    return list_package_queue(db)


@router.post("/", response_model=PackageCreateResponse)
def create_package_record(
    payload: PackageCreateRequest,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_roles("intake", "admin")),
) -> PackageCreateResponse:
    """Create a new onboarding package and place it into processing."""
    response = create_package(db, payload)
    record_audit_event(
        db, actor_id=actor.actor_id, actor_role=actor.role, action="package.created",
        package_id=response.package_id, resource_type="document_package", resource_id=response.package_id,
        event_metadata={"vendor_name": payload.vendor_name, "assigned_reviewer": payload.assigned_reviewer},
    )
    return response


@router.post("/{package_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    package_id: str,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_roles("intake", "admin")),
) -> DocumentUploadResponse:
    """Store one PDF supplied for an expected document type."""
    contents = await file.read()
    response = upload_document_file(
        db,
        package_id=package_id,
        doc_type=doc_type,
        file_name=file.filename or "uploaded-document.pdf",
        mime_type=file.content_type,
        contents=contents,
    )
    record_audit_event(
        db, actor_id=actor.actor_id, actor_role=actor.role, action="document.uploaded",
        package_id=package_id, resource_type="document", resource_id=response.document_id,
        event_metadata={"doc_type": response.doc_type, "file_name": response.file_name},
    )
    return response


@router.get("/{package_id}/documents/{document_id}/file")
def download_document(
    package_id: str, document_id: str, db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_roles("intake", "reviewer", "admin")),
) -> Response:
    """Return an uploaded file only when it belongs to the requested package."""
    contents, media_type, file_name = get_document_file(db, package_id, document_id)
    return Response(
        content=contents,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{file_name}"'},
    )


@router.post(
    "/{package_id}/field-overrides",
    response_model=FieldReviewOverrideCreateResponse,
)
def submit_field_override(
    package_id: str,
    payload: FieldReviewOverrideCreateRequest,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_roles("reviewer", "admin")),
) -> FieldReviewOverrideCreateResponse:
    """Append an auditable reviewer correction without overwriting extracted data."""
    payload.reviewer = actor.actor_id
    response = create_field_review_override(db, package_id, payload)
    record_audit_event(
        db, actor_id=actor.actor_id, actor_role=actor.role, action="field.override_created",
        package_id=package_id, resource_type="extracted_field", resource_id=response.field_id,
        event_metadata={"override_id": response.override_id},
    )
    return response


@router.post(
    "/{package_id}/finding-resolutions",
    response_model=FindingResolutionCreateResponse,
)
def submit_finding_resolution(
    package_id: str,
    payload: FindingResolutionCreateRequest,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_roles("reviewer", "admin")),
) -> FindingResolutionCreateResponse:
    """Record a reviewer resolution without deleting the original finding."""
    payload.reviewer = actor.actor_id
    response = create_finding_resolution(db, package_id, payload)
    record_audit_event(
        db, actor_id=actor.actor_id, actor_role=actor.role, action="finding.resolved",
        package_id=package_id, resource_type="validation_finding", resource_id=response.finding_id,
        event_metadata={"resolution_id": response.resolution_id, "status": response.finding_status},
    )
    return response


@router.get("/{package_id}", response_model=PackageDetailResponse)
def get_package(
    package_id: str, db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_roles("intake", "reviewer", "admin")),
) -> PackageDetailResponse:
    """Return packet review details for one vendor onboarding package."""
    return get_package_detail(db, package_id)


@router.post(
    "/{package_id}/simulate-processing",
    response_model=PackageSimulationResponse,
)
def simulate_processing(
    package_id: str, db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_roles("intake", "admin")),
) -> PackageSimulationResponse:
    """Advance a processing package into a review-ready state for demo purposes."""
    response = simulate_package_processing(db, package_id)
    record_audit_event(
        db, actor_id=actor.actor_id, actor_role=actor.role, action="package.processing_started",
        package_id=package_id, resource_type="document_package", resource_id=package_id,
        event_metadata={"mode": "demo"},
    )
    return response


@router.post("/{package_id}/process", response_model=PackageSimulationResponse)
def process_queued_package(
    package_id: str, db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_roles("intake", "admin")),
) -> PackageSimulationResponse:
    """Run one queued packet in local development without starting a persistent worker."""
    response = simulate_package_processing(db, package_id)
    record_audit_event(
        db, actor_id=actor.actor_id, actor_role=actor.role, action="package.processing_started",
        package_id=package_id, resource_type="document_package", resource_id=package_id,
        event_metadata={"mode": "manual"},
    )
    return response


@router.post("/{package_id}/decisions", response_model=ReviewDecisionCreateResponse)
def submit_review_decision(
    package_id: str,
    payload: ReviewDecisionCreateRequest,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_roles("reviewer", "admin")),
) -> ReviewDecisionCreateResponse:
    """Persist a reviewer decision for one onboarding package."""
    payload.reviewer = actor.actor_id
    response = create_review_decision(db, package_id, payload)
    record_audit_event(
        db, actor_id=actor.actor_id, actor_role=actor.role, action="review.decision_created",
        package_id=package_id, resource_type="review_decision", resource_id=response.decision_id,
        event_metadata={"final_decision": response.final_decision, "package_status": response.package_status},
    )
    return response
