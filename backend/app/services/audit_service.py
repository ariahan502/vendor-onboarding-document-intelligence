"""Append-only, hash-chained audit records for high-impact workflow actions."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.decisioning import AuditEvent


def record_audit_event(
    db: Session,
    *,
    actor_id: str,
    actor_role: str,
    action: str,
    package_id: str | None,
    resource_type: str,
    resource_id: str | None,
    event_metadata: dict[str, object] | None = None,
) -> AuditEvent:
    previous = db.scalar(
        select(AuditEvent).order_by(AuditEvent.created_at.desc(), AuditEvent.event_id.desc()).limit(1)
    )
    created_at = datetime.now(timezone.utc)
    payload = {
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "package_id": package_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "event_metadata": event_metadata or {},
        "previous_event_hash": previous.event_hash if previous else None,
        "created_at": created_at.isoformat(),
    }
    event = AuditEvent(
        event_id=f"audit_{uuid4().hex[:16]}",
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        package_id=package_id,
        resource_type=resource_type,
        resource_id=resource_id,
        event_metadata=event_metadata or {},
        previous_event_hash=previous.event_hash if previous else None,
        event_hash=sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        created_at=created_at,
    )
    db.add(event)
    db.commit()
    return event


def list_audit_events(db: Session, package_id: str | None = None) -> list[AuditEvent]:
    query = select(AuditEvent).order_by(AuditEvent.created_at.asc(), AuditEvent.event_id.asc())
    if package_id:
        query = query.where(AuditEvent.package_id == package_id)
    return list(db.scalars(query).all())
