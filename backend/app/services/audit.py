from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from backend.app.models.audit_logs import AuditLog

def create_audit_log(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: Optional[int],
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Utility function to write a mutating DB operation to the audit log.
    """
    db_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        details=details or {}
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log
