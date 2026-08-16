from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.deps import require_roles
from app.database import get_db
from app.models import (
    AuditLog, Citation, Collaboration, Conference, ConferenceParticipation,
    Institution, Project, ProjectMember, Publication, PublicationAuthor,
    Researcher, Tag, User,
)
from app.schemas.admin import UserAdminUpdate
from app.schemas.auth import UserOut
from app.schemas.common import ResearcherOut
from app.schemas.researcher import ResearcherUpdate

router = APIRouter(prefix="/admin", tags=["admin"])
system_admin_only = require_roles("system_admin")


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(system_admin_only)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserAdminUpdate, db: Session = Depends(get_db), current_user=Depends(system_admin_only)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    changed = payload.model_dump(exclude_unset=True)
    for field, value in changed.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    log_action(db, current_user.id, "UPDATE", "User", user.id, {"fields": list(changed.keys())})
    return user


@router.put("/researchers/{researcher_id}", response_model=ResearcherOut)
def admin_update_researcher(
    researcher_id: str, payload: ResearcherUpdate, db: Session = Depends(get_db), current_user=Depends(system_admin_only)
):
    researcher = db.get(Researcher, researcher_id)
    if not researcher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Researcher not found")

    if payload.orcid_id and payload.orcid_id != researcher.orcid_id:
        clash = db.query(Researcher).filter(Researcher.orcid_id == payload.orcid_id).first()
        if clash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ORCID ID is already in use")

    changed = payload.model_dump(exclude_unset=True)
    for field, value in changed.items():
        setattr(researcher, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not update researcher")
    db.refresh(researcher)
    log_action(db, current_user.id, "UPDATE", "Researcher", researcher.id, {"fields": list(changed.keys())})
    return researcher


# ============================================================
# ACTIVITY LOGS
# ============================================================
@router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(system_admin_only),
):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(AuditLog).count()
    results = []
    for log in logs:
        user = db.get(User, log.user_id) if log.user_id else None
        results.append({
            "id": str(log.id),
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "user_email": user.email if user else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })
    return {"total": total, "logs": results}


# ============================================================
# RAW TABLE BROWSER (read-only, whitelisted tables only)
# ============================================================
TABLE_REGISTRY = {
    "users": User,
    "institutions": Institution,
    "researchers": Researcher,
    "tags": Tag,
    "publications": Publication,
    "publication_authors": PublicationAuthor,
    "projects": Project,
    "project_members": ProjectMember,
    "collaborations": Collaboration,
    "conferences": Conference,
    "conference_participations": ConferenceParticipation,
    "citations": Citation,
    "audit_logs": AuditLog,
}


def _serialize_value(v):
    if isinstance(v, (UUID,)):
        return str(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if hasattr(v, "value") and not isinstance(v, (int, str, bool)):
        return v.value  # enum
    return v


@router.get("/tables")
def list_tables(db: Session = Depends(get_db), _=Depends(system_admin_only)):
    counts = {}
    for name, model in TABLE_REGISTRY.items():
        counts[name] = db.query(model).count()
    return {"tables": counts}


@router.get("/tables/{table_name}")
def browse_table(
    table_name: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(system_admin_only),
):
    model = TABLE_REGISTRY.get(table_name)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown table '{table_name}'. Allowed: {', '.join(TABLE_REGISTRY.keys())}")

    mapper = inspect(model)
    columns = [c.key for c in mapper.column_attrs]

    total = db.query(model).count()
    rows = db.query(model).offset(offset).limit(limit).all()

    serialized = []
    for row in rows:
        serialized.append({col: _serialize_value(getattr(row, col)) for col in columns})

    return {"table": table_name, "columns": columns, "total": total, "rows": serialized}