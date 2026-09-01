from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.models.project import Project
from app.models.researcher import Researcher
from sqlalchemy import or_
from app.Schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.Crud.audit import log_action

router = APIRouter(prefix="/projects", tags=["Projects"])

def result(item: Project):
    return {**{field: getattr(item, field) for field in ("id", "owner_id", "title", "description", "research_area", "status", "start_date", "end_date")}, "researcher_ids": [member.id for member in item.researchers], "member_count": len(item.researchers)}

@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Project)
    if user.role == "Institution Admin":
        if not user.institution_id: raise HTTPException(403, "Your account is not assigned to an institution.")
        query = query.join(User, Project.owner_id == User.id).filter(User.institution_id == user.institution_id)
    elif user.role not in {"Admin", "System Admin"}:
        query = query.filter(or_(Project.owner_id == user.id, Project.researchers.any(Researcher.user_id == user.id)))
    return [result(item) for item in query.order_by(Project.start_date.desc().nullslast(), Project.title).all()]

@router.get("/my", response_model=list[ProjectResponse])
def my_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [result(item) for item in db.query(Project).filter(Project.owner_id == user.id).order_by(Project.start_date.desc().nullslast()).all()]

@router.get("/admin/all", response_model=list[ProjectResponse])
def admin_projects(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return [result(item) for item in db.query(Project).order_by(Project.start_date.desc().nullslast()).all()]

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Project).filter(Project.id == project_id).first()
    if not item: raise HTTPException(404, "Project not found.")
    if user.role == "Institution Admin" and (not item.owner or item.owner.institution_id != user.institution_id):
        raise HTTPException(403, "You can only view projects from your institution.")
    if user.role not in {"Admin", "System Admin", "Institution Admin"} and item.owner_id != user.id and not any(member.user_id == user.id for member in item.researchers):
        raise HTTPException(403, "You can only view projects you own or are assigned to.")
    return result(item)

@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"Researcher", "Faculty", "Admin", "System Admin", "Institution Admin"}: raise HTTPException(403, "Your role cannot create projects.")
    item = Project(**data.model_dump(), owner_id=user.id); db.add(item); db.flush(); log_action(db, "PROJECT_CREATED", user.id, "Project", item.id, item.title); db.commit(); db.refresh(item); return result(item)

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Project).filter(Project.id == project_id).first()
    if not item: raise HTTPException(404, "Project not found.")
    is_institution_manager = user.role == "Institution Admin" and item.owner and item.owner.institution_id == user.institution_id
    if item.owner_id != user.id and user.role not in {"Admin", "System Admin"} and not is_institution_manager: raise HTTPException(403, "You can only edit projects you own or manage for your institution.")
    for field, value in data.model_dump(exclude_unset=True).items(): setattr(item, field, value)
    log_action(db, "PROJECT_UPDATED", user.id, "Project", item.id, item.title); db.commit(); db.refresh(item); return result(item)

@router.post("/{project_id}/assignments", response_model=ProjectResponse)
def add_assignment(project_id: int, researcher_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Project).filter(Project.id == project_id).first()
    researcher = db.query(Researcher).filter(Researcher.id == researcher_id).first()
    if not item or not researcher: raise HTTPException(404, "Project or researcher not found.")
    is_institution_manager = user.role == "Institution Admin" and item.owner and item.owner.institution_id == user.institution_id
    if user.role == "Institution Admin" and researcher.institution_id != user.institution_id: raise HTTPException(403, "You can only assign researchers from your institution.")
    if item.owner_id != user.id and user.role not in {"Admin", "System Admin"} and not is_institution_manager: raise HTTPException(403, "Only the project owner or institution manager can manage its team.")
    if researcher not in item.researchers: item.researchers.append(researcher)
    log_action(db, "PROJECT_MEMBER_ASSIGNED", user.id, "Project", item.id, researcher.name); db.commit(); db.refresh(item)
    return result(item)

@router.delete("/{project_id}/assignments/{researcher_id}", response_model=ProjectResponse)
def remove_assignment(project_id: int, researcher_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Project).filter(Project.id == project_id).first()
    researcher = db.query(Researcher).filter(Researcher.id == researcher_id).first()
    if not item or not researcher: raise HTTPException(404, "Project or researcher not found.")
    is_institution_manager = user.role == "Institution Admin" and item.owner and item.owner.institution_id == user.institution_id
    if user.role == "Institution Admin" and researcher.institution_id != user.institution_id: raise HTTPException(403, "You can only manage researchers from your institution.")
    if item.owner_id != user.id and user.role not in {"Admin", "System Admin"} and not is_institution_manager: raise HTTPException(403, "Only the project owner or institution manager can manage its team.")
    if researcher in item.researchers: item.researchers.remove(researcher)
    log_action(db, "PROJECT_MEMBER_REMOVED", user.id, "Project", item.id, researcher.name); db.commit(); db.refresh(item)
    return result(item)

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Project).filter(Project.id == project_id).first()
    if not item: raise HTTPException(404, "Project not found.")
    is_institution_manager = user.role == "Institution Admin" and item.owner and item.owner.institution_id == user.institution_id
    if item.owner_id != user.id and user.role not in {"Admin", "System Admin"} and not is_institution_manager: raise HTTPException(403, "You can only delete projects you own or manage for your institution.")
    log_action(db, "PROJECT_DELETED", user.id, "Project", item.id, item.title); db.delete(item); db.commit(); return Response(status_code=204)
