from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.institutions import Institution
from backend.app.schemas.institutions import InstitutionCreate, InstitutionUpdate, InstitutionOut
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/institutions/", response_model=List[InstitutionOut])
def read_institutions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve institutions list.
    """
    query = db.query(Institution)
    if search:
        query = query.filter(Institution.name.ilike(f"%{search}%"))
    institutions = query.offset(skip).limit(limit).all()
    return institutions

@router.get("/institutions/{id}", response_model=InstitutionOut)
def read_institution(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get institution by id.
    """
    institution = db.query(Institution).filter(Institution.id == id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution

@router.post("/institutions/", response_model=InstitutionOut, status_code=status.HTTP_201_CREATED)
def create_institution(
    *,
    db: Session = Depends(get_db),
    institution_in: InstitutionCreate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Create dynamic institution. (Admin only)
    """
    db_institution = Institution(
        name=institution_in.name,
        type=institution_in.type,
        address=institution_in.address,
        website=institution_in.website
    )
    db.add(db_institution)
    db.commit()
    db.refresh(db_institution)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="institution",
        entity_id=db_institution.id,
        ip_address=request.client.host if request.client else None
    )
    return db_institution

@router.put("/institutions/{id}", response_model=InstitutionOut)
def update_institution(
    *,
    db: Session = Depends(get_db),
    id: int,
    institution_in: InstitutionUpdate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Update institution data. (Admin only)
    """
    institution = db.query(Institution).filter(Institution.id == id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
        
    update_data = institution_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(institution, field, update_data[field])
        
    db.add(institution)
    db.commit()
    db.refresh(institution)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="institution",
        entity_id=institution.id,
        ip_address=request.client.host if request.client else None
    )
    return institution

@router.delete("/institutions/{id}")
def delete_institution(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(RoleChecker([UserRole.system_admin])),
    request: Request
) -> Any:
    """
    Delete institution. (System Admin only)
    """
    institution = db.query(Institution).filter(Institution.id == id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    db.delete(institution)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="institution",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Institution deleted successfully"}
