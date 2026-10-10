from typing import Any

from sqlalchemy.orm import Session

from studio.db.models import AuditLog


def record(
    session: Session,
    entity_type: str,
    entity_id: object,
    action: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Append an audit entry. Callers must never pass secrets in `details`."""
    session.add(
        AuditLog(
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            details=details or {},
        )
    )
