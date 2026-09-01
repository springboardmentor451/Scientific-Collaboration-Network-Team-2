from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.models.audit import AuditLog
from app.Schemas.admin import AuditResponse

router = APIRouter(prefix="/admin/audit", tags=["Admin"])

@router.get("", response_model=list[AuditResponse])
def get_audit_logs(search: str | None = None, action: str | None = None, skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    query = db.query(AuditLog)
    if action: query = query.filter(AuditLog.action == action)
    if search: query = query.filter((AuditLog.action.ilike(f"%{search}%")) | (AuditLog.details.ilike(f"%{search}%")))
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
