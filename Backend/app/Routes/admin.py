from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_admin
from app.Crud.audit import log_action
from app.models.user import User
from app.models.researcher import Researcher
from app.models.publication import Publication
from app.models.collaboration import CollaborationRequest
from app.models.institution import Institution
from app.models.conference import Conference
from app.models.project import Project
from app.Schemas.admin import AdminUserResponse, UserApprovalUpdate, UserRoleUpdate, UserStatusUpdate
from app.Schemas.researcher import ResearcherResponse
from app.Schemas.publication import PublicationResponse
from app.Schemas.collaboration import CollaborationRequestResponse
from app.Routes.researcher import researcher_response

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/statistics")
def statistics(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    roles = {role: count for role, count in db.query(User.role, func.count(User.id)).group_by(User.role).all()}
    return {"total_users": db.query(User).count(), "active_users": db.query(User).filter(User.is_active.is_(True)).count(), "inactive_users": db.query(User).filter(User.is_active.is_(False)).count(), "total_researchers": db.query(Researcher).count(), "total_publications": db.query(Publication).count(), "total_institutions": db.query(Institution).count(), "total_conferences": db.query(Conference).count(), "collaboration_requests": db.query(CollaborationRequest).count(), "accepted_collaborations": db.query(CollaborationRequest).filter(CollaborationRequest.status == "Accepted").count(), "role_distribution": roles, "recent_users": [AdminUserResponse.model_validate(user) for user in db.query(User).order_by(User.created_at.desc()).limit(5).all()]}

@router.get("/users", response_model=list[AdminUserResponse])
def users(search: str | None = Query(default=None), role: str | None = Query(default=None), db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    query = db.query(User)
    if search: query = query.filter(or_(User.full_name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))
    if role: query = query.filter(User.role == role)
    return query.order_by(User.created_at.desc()).all()

@router.get("/users/{user_id}", response_model=AdminUserResponse)
def user_detail(user_id: int, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found.")
    return user

@router.put("/users/{user_id}/status", response_model=AdminUserResponse)
def change_status(user_id: int, data: UserStatusUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found.")
    if user.id == admin.id and not data.is_active: raise HTTPException(400, "You cannot deactivate your own Admin account.")
    user.is_active = data.is_active; log_action(db, "USER_STATUS_CHANGED", admin.id, "User", user.id, f"Active: {data.is_active}"); db.commit(); db.refresh(user); return user

@router.put("/users/{user_id}/role", response_model=AdminUserResponse)
def change_role(user_id: int, data: UserRoleUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found.")
    if user.id == admin.id and data.role not in {"Admin", "System Admin"}: raise HTTPException(400, "You cannot remove your own Admin role.")
    old = user.role; user.role = data.role; log_action(db, "USER_ROLE_CHANGED", admin.id, "User", user.id, f"{old} to {data.role}"); db.commit(); db.refresh(user); return user

@router.put("/users/{user_id}/approval", response_model=AdminUserResponse)
def change_approval(user_id: int, data: UserApprovalUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found.")
    user.approval_status = data.approval_status
    if data.approval_status == "Rejected": user.is_active = False
    if data.approval_status == "Approved": user.is_active = True
    log_action(db, "USER_APPROVAL_CHANGED", admin.id, "User", user.id, data.approval_status); db.commit(); db.refresh(user); return user

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found.")
    if user.id == admin.id: raise HTTPException(400, "You cannot delete your own Admin account.")
    log_action(db, "USER_DELETED", admin.id, "User", user.id, user.email); db.delete(user); db.commit(); return Response(status_code=204)

@router.get("/researchers", response_model=list[ResearcherResponse])
def researchers(db: Session = Depends(get_db), _admin: User = Depends(require_admin)): return [researcher_response(db, item) for item in db.query(Researcher).order_by(Researcher.name).all()]

@router.delete("/researchers/{item_id}", status_code=204)
def delete_researcher(item_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    item=db.query(Researcher).filter(Researcher.id==item_id).first()
    if not item: raise HTTPException(404,"Researcher not found.")
    log_action(db,"RESEARCHER_DELETED",admin.id,"Researcher",item.id,item.name);db.delete(item);db.commit();return Response(status_code=204)

@router.get("/publications", response_model=list[PublicationResponse])
def publications(db: Session = Depends(get_db), _admin: User = Depends(require_admin)): return db.query(Publication).order_by(Publication.publication_year.desc()).all()

@router.delete("/publications/{item_id}", status_code=204)
def delete_publication(item_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    item=db.query(Publication).filter(Publication.id==item_id).first()
    if not item: raise HTTPException(404,"Publication not found.")
    log_action(db,"PUBLICATION_DELETED",admin.id,"Publication",item.id,item.title);db.delete(item);db.commit();return Response(status_code=204)

@router.get("/collaborations", response_model=list[CollaborationRequestResponse])
def collaborations(db: Session = Depends(get_db), _admin: User = Depends(require_admin)): return db.query(CollaborationRequest).order_by(CollaborationRequest.created_at.desc()).all()

@router.get("/data-quality")
def data_quality(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Live, non-destructive data quality indicators for the admin dashboard."""
    return {
        "users_without_institution": db.query(User).filter(User.institution_id.is_(None), User.role != "System Admin").count(),
        "researchers_without_user": db.query(Researcher).filter(Researcher.user_id.is_(None)).count(),
        "publications_without_doi": db.query(Publication).filter((Publication.doi_url.is_(None)) | (Publication.doi_url == "")).count(),
        "projects_without_dates": db.query(Project).filter(Project.start_date.is_(None)).count(),
        "pending_accounts": db.query(User).filter(User.approval_status == "Pending").count(),
    }
