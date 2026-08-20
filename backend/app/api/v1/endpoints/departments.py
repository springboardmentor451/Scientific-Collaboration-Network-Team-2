from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.departments import Department
from backend.app.schemas.departments import DepartmentCreate, DepartmentUpdate, DepartmentOut
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/departments/", response_model=List[DepartmentOut])
def read_departments(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    institution_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve departments.
    """
    query = db.query(Department)
    if institution_id:
        query = query.filter(Department.institution_id == institution_id)
    departments = query.offset(skip).limit(limit).all()
    return departments

@router.get("/departments/{id}", response_model=DepartmentOut)
def read_department(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get department by id.
    """
    department = db.query(Department).filter(Department.id == id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department

@router.post("/departments/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    *,
    db: Session = Depends(get_db),
    department_in: DepartmentCreate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Create department. (Admin only)
    """
    db_department = Department(
        institution_id=department_in.institution_id,
        name=department_in.name
    )
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="department",
        entity_id=db_department.id,
        ip_address=request.client.host if request.client else None
    )
    return db_department

@router.put("/departments/{id}", response_model=DepartmentOut)
def update_department(
    *,
    db: Session = Depends(get_db),
    id: int,
    department_in: DepartmentUpdate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Update department. (Admin only)
    """
    department = db.query(Department).filter(Department.id == id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
        
    update_data = department_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(department, field, update_data[field])
        
    db.add(department)
    db.commit()
    db.refresh(department)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="department",
        entity_id=department.id,
        ip_address=request.client.host if request.client else None
    )
    return department

@router.delete("/departments/{id}")
def delete_department(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(RoleChecker([UserRole.system_admin])),
    request: Request
) -> Any:
    """
    Delete department. (Admin only)
    """
    department = db.query(Department).filter(Department.id == id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    db.delete(department)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="department",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Department deleted successfully"}
