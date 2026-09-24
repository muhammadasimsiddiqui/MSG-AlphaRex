from sqlalchemy.orm import Session

from ..models import AuditEvent


def record_audit(db: Session, actor: str, action: str, entity_type: str, entity_id: str, detail: dict | None = None) -> None:
    db.add(AuditEvent(actor=actor, action=action, entity_type=entity_type, entity_id=entity_id, detail=detail or {}))
