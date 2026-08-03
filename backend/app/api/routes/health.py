from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.storage import StorageConfigurationError, get_document_storage


router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """Confirm database and configured document storage are available."""
    try:
        db.execute(text("SELECT 1"))
        get_document_storage().healthcheck()
    except Exception as exc:
        detail = "Document storage is unavailable." if isinstance(exc, StorageConfigurationError) else "A required dependency is unavailable."
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail) from exc
    return {"status": "ready"}
