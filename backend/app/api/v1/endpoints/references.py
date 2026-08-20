from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.researchers import Researcher
from backend.app.models.publications import Publication
from backend.app.models.references import Reference
from backend.app.schemas.references import ReferenceCreate, ReferenceUpdate, ReferenceOut
from backend.app.api.deps import get_current_active_user
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/references/", response_model=List[ReferenceOut])
def read_references(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    publication_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve references list.
    """
    query = db.query(Reference)
    if publication_id:
        query = query.filter(Reference.publication_id == publication_id)
    return query.offset(skip).limit(limit).all()

@router.get("/references/{id}", response_model=ReferenceOut)
def read_reference(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get reference entry by id.
    """
    ref = db.query(Reference).filter(Reference.id == id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")
    return ref

@router.post("/references/", response_model=ReferenceOut, status_code=status.HTTP_201_CREATED)
def create_reference(
    *,
    db: Session = Depends(get_db),
    ref_in: ReferenceCreate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Add a reference entry to a paper. (Only publication creator or admin)
    """
    pub = db.query(Publication).filter(Publication.id == ref_in.publication_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
        
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if pub.created_by != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=403,
            detail="Only the author of the publication or administrators can add references."
        )
        
    db_ref = Reference(
        publication_id=ref_in.publication_id,
        reference_text=ref_in.reference_text,
        doi=ref_in.doi,
        external_url=ref_in.external_url
    )
    db.add(db_ref)
    db.commit()
    db.refresh(db_ref)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="add_reference",
        entity_type="reference",
        entity_id=db_ref.id,
        ip_address=request.client.host if request.client else None
    )
    return db_ref

@router.put("/references/{id}", response_model=ReferenceOut)
def update_reference(
    *,
    db: Session = Depends(get_db),
    id: int,
    ref_in: ReferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Update reference entry details.
    """
    ref = db.query(Reference).filter(Reference.id == id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference entry not found")
        
    pub = ref.publication
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if pub.created_by != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=403,
            detail="Only the author of the publication or administrators can update references."
        )
        
    update_data = ref_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(ref, field, update_data[field])
        
    db.add(ref)
    db.commit()
    db.refresh(ref)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update_reference",
        entity_type="reference",
        entity_id=ref.id,
        ip_address=request.client.host if request.client else None
    )
    return ref

@router.delete("/references/{id}")
def delete_reference(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Delete reference entry.
    """
    ref = db.query(Reference).filter(Reference.id == id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference entry not found")
        
    pub = ref.publication
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if pub.created_by != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=403,
            detail="Only the author of the publication or administrators can delete references."
        )
        
    db.delete(ref)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete_reference",
        entity_type="reference",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Reference entry deleted successfully"}
