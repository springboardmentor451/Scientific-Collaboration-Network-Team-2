from datetime import date, datetime
from decimal import Decimal
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.config import get_settings
from app.core.deps import require_roles
from app.core.email import send_password_reset_email
from app.core.security import create_password_reset_token, hash_password
from app.database import get_db
from app.models import (
    AuditLog, Citation, Collaboration, Conference, ConferenceParticipation,
    Institution, Project, ProjectMember, Publication, PublicationAuthor,
    Researcher, Tag, User, UserRole,
)
from app.schemas.admin import UserAdminUpdate
from app.schemas.auth import UserOut
from app.schemas.common import ResearcherOut
from app.schemas.researcher import ResearcherUpdate

router = APIRouter(prefix="/admin", tags=["admin"])
system_admin_only = require_roles("system_admin")
admin_or_institution_admin = require_roles("system_admin", "institution_admin")
settings = get_settings()


class AdminCreateResearcher(BaseModel):
    email: EmailStr
    full_name: str
    department: str | None = None
    academic_title: str | None = None
    institution_id: UUID | None = None


@router.post("/researchers", response_model=ResearcherOut, status_code=status.HTTP_201_CREATED)
def admin_create_researcher(
    payload: AdminCreateResearcher,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_institution_admin),
):
    """
    System Admin / Institution Admin onboarding: creates a full user account
    + researcher profile in one step, then emails the new researcher a real
    password-reset link so they set their own password on first login
    (mirrors /auth/forgot-password — same token + email plumbing).
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists")

    user = User(
        email=payload.email,
        hashed_password=hash_password(secrets.token_urlsafe(32)),  # unusable placeholder — replaced via the emailed reset link
        role=UserRole.RESEARCHER,
        is_verified=True,
    )
    db.add(user)
    db.flush()

    researcher = Researcher(
        user_id=user.id,
        full_name=payload.full_name,
        department=payload.department,
        academic_title=payload.academic_title,
        institution_id=payload.institution_id,
    )
    db.add(researcher)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create researcher")
    db.refresh(researcher)

    reset_token = create_password_reset_token(str(user.id))
    reset_link = f"{settings.API_BASE_URL}/auth/reset-password?token={reset_token}"
    send_password_reset_email(user.email, reset_link)

    log_action(db, current_user.id, "CREATE", "Researcher", researcher.id, {"email": payload.email})
    return researcher


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


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db), current_user=Depends(system_admin_only)):
    """
    Permanently deletes an account (and, via ON DELETE CASCADE, their
    researcher profile). Publications/projects/citations they authored are
    NOT deleted — those stay in the system as historical records; only the
    login account and researcher profile row go away.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can't delete your own account while logged in as it.")

    if user.role == UserRole.SYSTEM_ADMIN:
        remaining_admins = (
            db.query(User)
            .filter(User.role == UserRole.SYSTEM_ADMIN, User.is_active == True, User.id != user.id)  # noqa: E712
            .count()
        )
        if remaining_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can't delete the last active System Admin account — the platform would have no admin left.",
            )

    log_action(db, current_user.id, "DELETE", "User", user.id, {"email": user.email})
    db.delete(user)
    db.commit()


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