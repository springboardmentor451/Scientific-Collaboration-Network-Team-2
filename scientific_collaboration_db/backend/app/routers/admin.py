import csv
import io
from datetime import date, datetime
from decimal import Decimal
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
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
    PublicationReview, Researcher, ReviewStatus, Tag, User, UserRole,
)
from app.schemas.admin import StaffAccountCreate, UserAdminUpdate
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

    An Institution Admin can only onboard researchers into their own
    institution — the institution_id they pass is ignored in favor of
    their own, so they can't quietly attach a researcher elsewhere.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists")

    institution_id = payload.institution_id
    if current_user.role == UserRole.INSTITUTION_ADMIN:
        if not current_user.effective_institution_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account isn't linked to an institution yet")
        institution_id = current_user.effective_institution_id

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
        institution_id=institution_id,
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


@router.post("/staff", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def admin_create_staff(
    payload: StaffAccountCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_institution_admin),
):
    """
    Onboards a Reviewer or Institution Admin account (no Researcher profile —
    these roles are scoped to an institution via User.institution_id instead).
    Emails a real password-reset link, same as /admin/researchers.

    An Institution Admin may only create Reviewer accounts, and only for
    their own institution. A System Admin can create either role, for any
    institution.
    """
    if payload.role not in (UserRole.REVIEWER, UserRole.INSTITUTION_ADMIN):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="role must be 'reviewer' or 'institution_admin'")

    institution_id = payload.institution_id
    if current_user.role == UserRole.INSTITUTION_ADMIN:
        if payload.role != UserRole.REVIEWER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Institution Admins can only create Reviewer accounts")
        if not current_user.effective_institution_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account isn't linked to an institution yet")
        institution_id = current_user.effective_institution_id
    elif institution_id and not db.get(Institution, institution_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="institution_id does not exist")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists")

    user = User(
        email=payload.email,
        hashed_password=hash_password(secrets.token_urlsafe(32)),
        role=payload.role,
        institution_id=institution_id,
        is_verified=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create account")
    db.refresh(user)

    reset_token = create_password_reset_token(str(user.id))
    reset_link = f"{settings.API_BASE_URL}/auth/reset-password?token={reset_token}"
    send_password_reset_email(user.email, reset_link)

    log_action(db, current_user.id, "CREATE", "User", user.id, {"email": payload.email, "role": payload.role.value})
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user=Depends(admin_or_institution_admin)):
    """
    System Admin sees every account. Institution Admin sees only accounts
    scoped to their own institution (researchers via their profile, plus
    reviewer/institution_admin staff via User.institution_id) — never other
    institutions' people, and never other System Admins.
    """
    query = db.query(User)
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return query.order_by(User.created_at.desc()).all()

    inst_id = current_user.effective_institution_id
    if not inst_id:
        return []
    users = query.order_by(User.created_at.desc()).all()
    return [
        u for u in users
        if u.role != UserRole.SYSTEM_ADMIN and u.effective_institution_id == inst_id
    ]


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserAdminUpdate, db: Session = Depends(get_db), current_user=Depends(admin_or_institution_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    changed = payload.model_dump(exclude_unset=True)

    if current_user.role == UserRole.INSTITUTION_ADMIN:
        # Institution Admins may only manage accounts in their own
        # institution, may only switch someone between Researcher and
        # Reviewer (never promote to Institution Admin / System Admin, and
        # never move someone to a different institution), and may toggle
        # whether the account is active.
        if user.role not in (UserRole.RESEARCHER, UserRole.REVIEWER) or user.effective_institution_id != current_user.effective_institution_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only manage Researcher/Reviewer accounts in your own institution")
        allowed_fields = {"is_active", "role"}
        disallowed = set(changed.keys()) - allowed_fields
        if disallowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Institution Admins can only toggle active status or switch someone between Researcher and Reviewer")
        if "role" in changed and changed["role"] not in (UserRole.RESEARCHER, UserRole.REVIEWER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Institution Admins can only switch a user between Researcher and Reviewer")
        if "institution_id" in changed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Institution Admins cannot reassign a user's institution")

    # Capture the institution a role-change is happening FROM, before we
    # touch anything — effective_institution_id's answer depends on the
    # user's *current* role (Researchers read it off their Researcher
    # profile; everyone else reads User.institution_id directly). Without
    # this snapshot, flipping role -> reviewer for someone who only ever had
    # a Researcher profile would silently strand them with no institution at
    # all afterward, since User.institution_id was never populated for them.
    prior_effective_institution_id = user.effective_institution_id

    for field, value in changed.items():
        setattr(user, field, value)

    if changed.get("role") in (UserRole.REVIEWER, UserRole.INSTITUTION_ADMIN) and user.institution_id is None:
        user.institution_id = prior_effective_institution_id

    cancelled_reviews = 0
    if user.role == UserRole.REVIEWER and changed.get("is_active") is False:
        # Suspending a reviewer shouldn't leave publications silently stuck
        # waiting on someone who can no longer act on them. Their undecided
        # assignments are cancelled outright (not left pending, not silently
        # reassigned to someone else who never agreed to take them) so an
        # admin sees the gap and can assign a replacement deliberately.
        pending = db.query(PublicationReview).filter(
            PublicationReview.reviewer_id == user.id,
            PublicationReview.status == ReviewStatus.PENDING,
        ).all()
        cancelled_reviews = len(pending)
        for r in pending:
            db.delete(r)

    db.commit()
    db.refresh(user)
    log_action(db, current_user.id, "UPDATE", "User", user.id, {
        "fields": list(changed.keys()),
        **({"cancelled_pending_reviews": cancelled_reviews} if cancelled_reviews else {}),
    })
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
    researcher_id: str, payload: ResearcherUpdate, db: Session = Depends(get_db), current_user: User = Depends(admin_or_institution_admin)
):
    researcher = db.get(Researcher, researcher_id)
    if not researcher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Researcher not found")

    changed = payload.model_dump(exclude_unset=True)

    if current_user.role == UserRole.INSTITUTION_ADMIN:
        # Institution Admins may edit a researcher's profile details, but
        # only for researchers already in their own institution, and they
        # may not move a researcher to a different institution — that stays
        # a System Admin action, same as reassigning any other account.
        admin_inst = current_user.effective_institution_id
        if not admin_inst or researcher.institution_id != admin_inst:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit researchers in your own institution")
        if "institution_id" in changed and changed["institution_id"] != admin_inst:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Institution Admins cannot move a researcher to a different institution")

    if payload.orcid_id and payload.orcid_id != researcher.orcid_id:
        clash = db.query(Researcher).filter(Researcher.orcid_id == payload.orcid_id).first()
        if clash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ORCID ID is already in use")

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
    current_user: User = Depends(admin_or_institution_admin),
):
    """
    System Admin sees every action on the platform. Institution Admin sees
    only actions performed BY people who belong to their own institution
    (themselves, their researchers, and their reviewers) — a scoped audit
    trail of "what my institution's accounts have been doing", not the
    whole platform's activity.
    """
    query = db.query(AuditLog)

    if current_user.role == UserRole.INSTITUTION_ADMIN:
        inst_id = current_user.effective_institution_id
        if not inst_id:
            return {"total": 0, "logs": []}
        institution_user_ids = [
            u.id for u in db.query(User).all()
            if u.role != UserRole.SYSTEM_ADMIN and u.effective_institution_id == inst_id
        ]
        if not institution_user_ids:
            return {"total": 0, "logs": []}
        query = query.filter(AuditLog.user_id.in_(institution_user_ids))

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
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


# Tables an Institution Admin is allowed to browse at all. "institutions"
# and "users" are included but row-filtered down to their own institution
# (see _institution_scoped_rows below) — everything else that has no
# institution concept at all (e.g. raw platform config) simply isn't
# exposed to them.
INSTITUTION_ADMIN_TABLES = {
    "institutions", "users", "researchers", "tags", "publications",
    "publication_authors", "projects", "project_members", "collaborations",
    "conferences", "conference_participations", "citations", "audit_logs",
}


def _institution_scoped_rows(table_name: str, rows: list, inst_id, db: Session) -> list:
    """
    Filters an already-fetched list of ORM rows down to just the ones that
    belong to an Institution Admin's own institution. Done in Python (not a
    SQL WHERE) so every table can reuse the same "which institution owns
    this row" rules already established elsewhere in this file (list_users,
    list_audit_logs) and in Publication.institution_name, without having to
    duplicate multi-table JOIN logic per table here.
    """
    inst_id = str(inst_id)

    def researcher_matches(researcher) -> bool:
        return bool(researcher and researcher.institution_id and str(researcher.institution_id) == inst_id)

    if table_name == "institutions":
        return [r for r in rows if str(r.id) == inst_id]
    if table_name == "users":
        return [r for r in rows if r.role != UserRole.SYSTEM_ADMIN and r.effective_institution_id and str(r.effective_institution_id) == inst_id]
    if table_name == "researchers":
        return [r for r in rows if researcher_matches(r)]
    if table_name == "tags":
        return rows  # global taxonomy, not institution-owned — safe to show in full
    if table_name == "publications":
        return [r for r in rows if any(researcher_matches(a.researcher) for a in r.authors)]
    if table_name == "publication_authors":
        return [r for r in rows if researcher_matches(r.researcher)]
    if table_name == "projects":
        return [
            r for r in rows
            if (r.lead_institution_id and str(r.lead_institution_id) == inst_id)
            or any(researcher_matches(m.researcher) for m in r.members)
        ]
    if table_name == "project_members":
        return [r for r in rows if researcher_matches(r.researcher)]
    if table_name == "collaborations":
        return [
            r for r in rows
            if (r.institution_a_id and str(r.institution_a_id) == inst_id)
            or (r.institution_b_id and str(r.institution_b_id) == inst_id)
        ]
    if table_name == "conferences":
        return [r for r in rows if r.institution_id and str(r.institution_id) == inst_id]
    if table_name == "conference_participations":
        return [r for r in rows if researcher_matches(r.researcher)]
    if table_name == "citations":
        return [
            r for r in rows
            if r.citing_publication and any(researcher_matches(a.researcher) for a in r.citing_publication.authors)
        ]
    if table_name == "audit_logs":
        kept = []
        for r in rows:
            u = db.get(User, r.user_id) if r.user_id else None
            if u and u.role != UserRole.SYSTEM_ADMIN and u.effective_institution_id and str(u.effective_institution_id) == inst_id:
                kept.append(r)
        return kept
    return []


def _rows_for_table(table_name: str, model, db: Session, current_user: User):
    """Returns the full (unpaginated) list of ORM rows this user may see for a table."""
    if table_name not in TABLE_REGISTRY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown table '{table_name}'. Allowed: {', '.join(TABLE_REGISTRY.keys())}")

    if current_user.role == UserRole.SYSTEM_ADMIN:
        return db.query(model).all()

    # Institution Admin
    if table_name not in INSTITUTION_ADMIN_TABLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this table")
    inst_id = current_user.effective_institution_id
    if not inst_id:
        return []
    return _institution_scoped_rows(table_name, db.query(model).all(), inst_id, db)


@router.get("/tables")
def list_tables(db: Session = Depends(get_db), current_user: User = Depends(admin_or_institution_admin)):
    counts = {}
    registry = TABLE_REGISTRY if current_user.role == UserRole.SYSTEM_ADMIN else {
        k: v for k, v in TABLE_REGISTRY.items() if k in INSTITUTION_ADMIN_TABLES
    }
    for name, model in registry.items():
        counts[name] = len(_rows_for_table(name, model, db, current_user))
    return {"tables": counts}


@router.get("/tables/{table_name}")
def browse_table(
    table_name: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_institution_admin),
):
    model = TABLE_REGISTRY.get(table_name)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown table '{table_name}'. Allowed: {', '.join(TABLE_REGISTRY.keys())}")

    mapper = inspect(model)
    columns = [c.key for c in mapper.column_attrs]

    all_rows = _rows_for_table(table_name, model, db, current_user)
    total = len(all_rows)
    rows = all_rows[offset:offset + limit]

    serialized = [{col: _serialize_value(getattr(row, col)) for col in columns} for row in rows]

    return {"table": table_name, "columns": columns, "total": total, "rows": serialized}


@router.get("/tables/{table_name}/export")
def export_table_csv(
    table_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_institution_admin),
):
    """
    Downloads the full (unpaginated) contents of a table as CSV — same
    permissions and same institution scoping as GET /admin/tables/{name},
    just without the 200-row page cap so the download is complete.
    """
    model = TABLE_REGISTRY.get(table_name)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown table '{table_name}'. Allowed: {', '.join(TABLE_REGISTRY.keys())}")

    mapper = inspect(model)
    columns = [c.key for c in mapper.column_attrs]
    rows = _rows_for_table(table_name, model, db, current_user)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_serialize_value(getattr(row, col)) for col in columns])

    log_action(db, current_user.id, "EXPORT", "TableCSV", None, {"table": table_name, "rows": len(rows)})

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{table_name}.csv"'},
    )