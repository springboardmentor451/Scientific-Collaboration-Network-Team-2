from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.projects import Project, ProjectStatus
from backend.app.schemas.projects import ProjectCreate, ProjectUpdate, ProjectOut
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/projects/", response_model=List[ProjectOut])
def read_projects(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[ProjectStatus] = None,
    institution_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve projects list.
    """
    query = db.query(Project)
    if status_filter:
        query = query.filter(Project.status == status_filter)
    if institution_id:
        query = query.filter(Project.institution_id == institution_id)
    if search:
        query = query.filter(
            (Project.title.ilike(f"%{search}%")) | 
            (Project.description.ilike(f"%{search}%"))
        )
    return query.offset(skip).limit(limit).all()

@router.get("/projects/{id}", response_model=ProjectOut)
def read_project(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get project details.
    """
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/projects/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    *,
    db: Session = Depends(get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Create a project record.
    """
    db_project = Project(
        title=project_in.title,
        description=project_in.description,
        funding_source=project_in.funding_source,
        funding_amount=project_in.funding_amount,
        start_date=project_in.start_date,
        end_date=project_in.end_date,
        status=project_in.status or ProjectStatus.proposed,
        institution_id=project_in.institution_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="project",
        entity_id=db_project.id,
        ip_address=request.client.host if request.client else None
    )
    return db_project

@router.put("/projects/{id}", response_model=ProjectOut)
def update_project(
    *,
    db: Session = Depends(get_db),
    id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Update project details.
    """
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    update_data = project_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(project, field, update_data[field])
        
    db.add(project)
    db.commit()
    db.refresh(project)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="project",
        entity_id=project.id,
        ip_address=request.client.host if request.client else None
    )
    return project

@router.delete("/projects/{id}")
def delete_project(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(RoleChecker([UserRole.system_admin])),
    request: Request
) -> Any:
    """
    Delete a project entry.
    """
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="project",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Project deleted successfully"}
