from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.audit_logs import AuditLog
from backend.app.schemas.audit_logs import AuditLogOut
from backend.app.api.deps import RoleChecker

router = APIRouter()

@router.get("/audit-logs/", response_model=List[AuditLogOut])
def read_audit_logs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    current_user: User = Depends(RoleChecker([UserRole.system_admin]))
) -> Any:
    """
    Retrieve system audit logs. (System Admin only)
    """
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
        
    # Order by newest logs first
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs
