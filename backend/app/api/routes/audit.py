from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth import CurrentActor, require_roles
from app.db.session import get_db
from app.schemas.packages import AuditEventSummary, AuditExportResponse
from app.services.audit_service import list_audit_events

router = APIRouter()


@router.get("/export", response_model=AuditExportResponse)
def export_audit_events(
    package_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_roles("admin")),
) -> AuditExportResponse:
    """Export the append-only audit ledger, including its hash-chain head."""
    events = list_audit_events(db, package_id)
    summaries = [
        AuditEventSummary(
            event_id=event.event_id,
            actor_id=event.actor_id,
            actor_role=event.actor_role,
            action=event.action,
            package_id=event.package_id,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            event_metadata=event.event_metadata,
            previous_event_hash=event.previous_event_hash,
            event_hash=event.event_hash,
            created_at=event.created_at,
        )
        for event in events
    ]
    return AuditExportResponse(
        generated_at=datetime.now(timezone.utc),
        event_count=len(summaries),
        chain_head=summaries[-1].event_hash if summaries else None,
        events=summaries,
    )
