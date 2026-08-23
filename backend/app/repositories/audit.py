from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def get_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
    path_contains: str | None = None,
):
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if path_contains:
        query = query.filter(AuditLog.path.contains(path_contains))
    return query.offset(skip).limit(limit).all()
