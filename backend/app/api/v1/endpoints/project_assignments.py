from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.project_assignments import ProjectAssignment
from backend.app.schemas.project_assignments import ProjectAssignmentCreate, ProjectAssignmentUpdate, ProjectAssignmentOut
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/project-assignments/", response_model=List[ProjectAssignmentOut])
def read_project_assignments(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    researcher_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve project assignments.
    """
    query = db.query(ProjectAssignment)
    if project_id:
        query = query.filter(ProjectAssignment.project_id == project_id)
    if researcher_id:
        query = query.filter(ProjectAssignment.researcher_id == researcher_id)
    return query.offset(skip).limit(limit).all()

@router.get("/project-assignments/{id}", response_model=ProjectAssignmentOut)
def read_project_assignment(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get assignment details.
    """
    assign = db.query(ProjectAssignment).filter(ProjectAssignment.id == id).first()
    if not assign:
        raise HTTPException(status_code=404, detail="Project assignment not found")
    return assign

@router.post("/project-assignments/", response_model=ProjectAssignmentOut, status_code=status.HTTP_201_CREATED)
def create_project_assignment(
    *,
    db: Session = Depends(get_db),
    assign_in: ProjectAssignmentCreate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Assign a researcher to a project. (Admin only)
    """
    # Check duplicate
    existing = db.query(ProjectAssignment).filter(
        ProjectAssignment.project_id == assign_in.project_id,
        ProjectAssignment.researcher_id == assign_in.researcher_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Researcher is already assigned to this project.")
        
    db_assign = ProjectAssignment(
        project_id=assign_in.project_id,
        researcher_id=assign_in.researcher_id,
        role_in_project=assign_in.role_in_project
    )
    db.add(db_assign)
    db.commit()
    db.refresh(db_assign)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="assign_project",
        entity_type="project_assignment",
        entity_id=db_assign.id,
        ip_address=request.client.host if request.client else None,
        details={"project_id": assign_in.project_id, "researcher_id": assign_in.researcher_id}
    )
    return db_assign

@router.put("/project-assignments/{id}", response_model=ProjectAssignmentOut)
def update_project_assignment(
    *,
    db: Session = Depends(get_db),
    id: int,
    assign_in: ProjectAssignmentUpdate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Update details of a project assignment. (Admin only)
    """
    assign = db.query(ProjectAssignment).filter(ProjectAssignment.id == id).first()
    if not assign:
        raise HTTPException(status_code=404, detail="Project assignment not found")
        
    update_data = assign_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(assign, field, update_data[field])
        
    db.add(assign)
    db.commit()
    db.refresh(assign)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update_assignment",
        entity_type="project_assignment",
        entity_id=assign.id,
        ip_address=request.client.host if request.client else None
    )
    return assign

@router.delete("/project-assignments/{id}")
def delete_project_assignment(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Remove a researcher from a project. (Admin only)
    """
    assign = db.query(ProjectAssignment).filter(ProjectAssignment.id == id).first()
    if not assign:
        raise HTTPException(status_code=404, detail="Project assignment not found")
    db.delete(assign)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="remove_assignment",
        entity_type="project_assignment",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Project assignment removed successfully"}
