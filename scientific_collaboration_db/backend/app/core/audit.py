"""
Lightweight audit logging. Call log_action() right after a successful
create/update/delete so there's a real, queryable history of who did what.

Failures here are swallowed (logged to stderr) so a logging problem never
breaks the actual user-facing action.
"""
import sys

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(db: Session, user_id, action: str, entity_type: str, entity_id, details: dict | None = None):
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details,
        )
        db.add(entry)
        db.commit()
    except Exception as exc:  # never let audit logging break the real request
        db.rollback()
        print(f"[audit] failed to log {action} {entity_type}:{entity_id} — {exc}", file=sys.stderr)