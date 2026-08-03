from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
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

router = APIRouter()


@router.get("/", response_model=PackageQueueResponse)
def list_packages(db: Session = Depends(get_db)) -> PackageQueueResponse:
    """Return queue data for the reviewer worklist."""
    return list_package_queue(db)


@router.post("/", response_model=PackageCreateResponse)
def create_package_record(
    payload: PackageCreateRequest, db: Session = Depends(get_db)
) -> PackageCreateResponse:
    """Create a new onboarding package and place it into processing."""
    return create_package(db, payload)


@router.post("/{package_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    package_id: str,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    """Store one PDF supplied for an expected document type."""
    contents = await file.read()
    return upload_document_file(
        db,
        package_id=package_id,
        doc_type=doc_type,
        file_name=file.filename or "uploaded-document.pdf",
        mime_type=file.content_type,
        contents=contents,
    )


@router.get("/{package_id}/documents/{document_id}/file")
def download_document(
    package_id: str, document_id: str, db: Session = Depends(get_db)
) -> FileResponse:
    """Return an uploaded file only when it belongs to the requested package."""
    file_path, media_type, file_name = get_document_file(db, package_id, document_id)
    return FileResponse(file_path, media_type=media_type, filename=file_name)


@router.post(
    "/{package_id}/field-overrides",
    response_model=FieldReviewOverrideCreateResponse,
)
def submit_field_override(
    package_id: str,
    payload: FieldReviewOverrideCreateRequest,
    db: Session = Depends(get_db),
) -> FieldReviewOverrideCreateResponse:
    """Append an auditable reviewer correction without overwriting extracted data."""
    return create_field_review_override(db, package_id, payload)


@router.post(
    "/{package_id}/finding-resolutions",
    response_model=FindingResolutionCreateResponse,
)
def submit_finding_resolution(
    package_id: str,
    payload: FindingResolutionCreateRequest,
    db: Session = Depends(get_db),
) -> FindingResolutionCreateResponse:
    """Record a reviewer resolution without deleting the original finding."""
    return create_finding_resolution(db, package_id, payload)


@router.get("/{package_id}", response_model=PackageDetailResponse)
def get_package(
    package_id: str, db: Session = Depends(get_db)
) -> PackageDetailResponse:
    """Return packet review details for one vendor onboarding package."""
    return get_package_detail(db, package_id)


@router.post(
    "/{package_id}/simulate-processing",
    response_model=PackageSimulationResponse,
)
def simulate_processing(
    package_id: str, db: Session = Depends(get_db)
) -> PackageSimulationResponse:
    """Advance a processing package into a review-ready state for demo purposes."""
    return simulate_package_processing(db, package_id)


@router.post("/{package_id}/process", response_model=PackageSimulationResponse)
def process_queued_package(
    package_id: str, db: Session = Depends(get_db)
) -> PackageSimulationResponse:
    """Run one queued packet in local development without starting a persistent worker."""
    return simulate_package_processing(db, package_id)


@router.post("/{package_id}/decisions", response_model=ReviewDecisionCreateResponse)
def submit_review_decision(
    package_id: str,
    payload: ReviewDecisionCreateRequest,
    db: Session = Depends(get_db),
) -> ReviewDecisionCreateResponse:
    """Persist a reviewer decision for one onboarding package."""
    return create_review_decision(db, package_id, payload)
