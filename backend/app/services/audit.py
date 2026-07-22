from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent
from app.models.user import User


def record_audit(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    detail: dict[str, Any] | None = None,
) -> AuditEvent:
    """Add an audit event to the session. The caller is responsible for commit."""
    event = AuditEvent(
        actor_id=actor.id if actor else None,
        actor_username=actor.username if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
    )
    db.add(event)
    return event
