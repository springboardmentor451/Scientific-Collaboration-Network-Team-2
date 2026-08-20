from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.collaborations import Collaboration, CollaborationType
from backend.app.schemas.collaborations import CollaborationCreate, CollaborationUpdate, CollaborationOut
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/collaborations/", response_model=List[CollaborationOut])
def read_collaborations(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    collab_type: Optional[CollaborationType] = None,
    researcher_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve collaborations list.
    """
    query = db.query(Collaboration)
    if collab_type:
        query = query.filter(Collaboration.collaboration_type == collab_type)
    if researcher_id:
        query = query.filter(
            (Collaboration.researcher_id_1 == researcher_id) | 
            (Collaboration.researcher_id_2 == researcher_id)
        )
    return query.offset(skip).limit(limit).all()

@router.get("/collaborations/{id}", response_model=CollaborationOut)
def read_collaboration(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get collaboration detail by id.
    """
    collab = db.query(Collaboration).filter(Collaboration.id == id).first()
    if not collab:
        raise HTTPException(status_code=404, detail="Collaboration record not found")
    return collab

@router.post("/collaborations/", response_model=CollaborationOut, status_code=status.HTTP_201_CREATED)
def create_collaboration(
    *,
    db: Session = Depends(get_db),
    collab_in: CollaborationCreate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.reviewer, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Create a collaboration entry.
    """
    db_collab = Collaboration(
        collaboration_type=collab_in.collaboration_type,
        researcher_id_1=collab_in.researcher_id_1,
        researcher_id_2=collab_in.researcher_id_2,
        institution_id_1=collab_in.institution_id_1,
        institution_id_2=collab_in.institution_id_2,
        project_id=collab_in.project_id,
        publication_id=collab_in.publication_id
    )
    db.add(db_collab)
    db.commit()
    db.refresh(db_collab)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="collaboration",
        entity_id=db_collab.id,
        ip_address=request.client.host if request.client else None
    )
    return db_collab

@router.put("/collaborations/{id}", response_model=CollaborationOut)
def update_collaboration(
    *,
    db: Session = Depends(get_db),
    id: int,
    collab_in: CollaborationUpdate,
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.reviewer, UserRole.institution_admin])),
    request: Request
) -> Any:
    """
    Update collaboration details.
    """
    collab = db.query(Collaboration).filter(Collaboration.id == id).first()
    if not collab:
        raise HTTPException(status_code=404, detail="Collaboration record not found")
        
    update_data = collab_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(collab, field, update_data[field])
        
    db.add(collab)
    db.commit()
    db.refresh(collab)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="collaboration",
        entity_id=collab.id,
        ip_address=request.client.host if request.client else None
    )
    return collab

@router.delete("/collaborations/{id}")
def delete_collaboration(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(RoleChecker([UserRole.system_admin])),
    request: Request
) -> Any:
    """
    Delete a collaboration entry.
    """
    collab = db.query(Collaboration).filter(Collaboration.id == id).first()
    if not collab:
        raise HTTPException(status_code=404, detail="Collaboration record not found")
    db.delete(collab)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="collaboration",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Collaboration record deleted successfully"}
