from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import get_db
from app.models.user import UserRole
from app.schemas.audit import AuditLogOut
from app.services import audit as audit_service

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit & Compliance"],
    dependencies=[Depends(require_roles(UserRole.SYSTEM_ADMIN))],
)


@router.get("/", response_model=list[AuditLogOut])
def read_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
    path_contains: str | None = None,
    db: Session = Depends(get_db),
):
    return audit_service.list_logs(db, skip, limit, user_id, path_contains)
