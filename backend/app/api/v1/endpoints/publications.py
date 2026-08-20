from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
import os

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.researchers import Researcher
from backend.app.models.publications import Publication, PublicationStatus, PublicationType
from backend.app.schemas.publications import PublicationCreate, PublicationUpdate, PublicationOut
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.utils.storage import get_storage
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/publications/", response_model=List[PublicationOut])
def read_publications(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[PublicationStatus] = None,
    type_filter: Optional[PublicationType] = None,
    created_by: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve publications list.
    """
    query = db.query(Publication)
    if status_filter:
        query = query.filter(Publication.status == status_filter)
    if type_filter:
        query = query.filter(Publication.type == type_filter)
    if created_by:
        query = query.filter(Publication.created_by == created_by)
    if search:
        query = query.filter(
            (Publication.title.ilike(f"%{search}%")) | 
            (Publication.abstract.ilike(f"%{search}%"))
        )
    # Role-based visibility check
    # Researchers can see all except other draft publications (can only see their own drafts)
    if current_user.role == UserRole.researcher:
        researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
        res_id = researcher.id if researcher else -1
        query = query.filter(
            (Publication.status != PublicationStatus.draft) | 
            (Publication.created_by == res_id)
        )
    
    publications = query.offset(skip).limit(limit).all()
    return publications

@router.get("/publications/{id}", response_model=PublicationOut)
def read_publication(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get publication detail.
    """
    pub = db.query(Publication).filter(Publication.id == id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
        
    # Draft protection
    if pub.status == PublicationStatus.draft:
        researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
        res_id = researcher.id if researcher else -1
        if pub.created_by != res_id and current_user.role != UserRole.system_admin:
            raise HTTPException(status_code=403, detail="Not authorized to access draft publication")
            
    return pub

@router.post("/publications/", response_model=PublicationOut, status_code=status.HTTP_201_CREATED)
def create_publication(
    *,
    db: Session = Depends(get_db),
    publication_in: PublicationCreate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Create a new publication entry.
    """
    # Fetch corresponding researcher profile
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    creator_id = researcher.id if researcher else None
    
    if current_user.role == UserRole.researcher and not creator_id:
        raise HTTPException(
            status_code=400,
            detail="A researcher profile is required to publish entries."
        )
        
    db_pub = Publication(
        title=publication_in.title,
        abstract=publication_in.abstract,
        type=publication_in.type or PublicationType.journal_paper,
        status=publication_in.status or PublicationStatus.draft,
        doi=publication_in.doi,
        venue=publication_in.venue,
        publication_date=publication_in.publication_date,
        file_url=publication_in.file_url,
        created_by=creator_id
    )
    db.add(db_pub)
    db.commit()
    db.refresh(db_pub)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="publication",
        entity_id=db_pub.id,
        ip_address=request.client.host if request.client else None
    )
    return db_pub

@router.put("/publications/{id}", response_model=PublicationOut)
def update_publication(
    *,
    db: Session = Depends(get_db),
    id: int,
    publication_in: PublicationUpdate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Update publication details.
    """
    pub = db.query(Publication).filter(Publication.id == id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
        
    # Access checks: owner, reviewer, or admin
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if pub.created_by != res_id and current_user.role not in [UserRole.system_admin, UserRole.reviewer, UserRole.institution_admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this publication entry."
        )
        
    update_data = publication_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(pub, field, update_data[field])
        
    db.add(pub)
    db.commit()
    db.refresh(pub)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="publication",
        entity_id=pub.id,
        ip_address=request.client.host if request.client else None
    )
    return pub

@router.delete("/publications/{id}")
def delete_publication(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Delete a publication entry.
    """
    pub = db.query(Publication).filter(Publication.id == id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
        
    # Access checks: owner or system_admin
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if pub.created_by != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this publication entry."
        )
        
    # Delete uploaded file from storage if present
    if pub.file_url:
        storage = get_storage()
        storage.delete_file(pub.file_url)
        
    db.delete(pub)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="publication",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Publication deleted successfully"}

@router.post("/publications/{id}/upload", response_model=PublicationOut)
async def upload_publication_file(
    *,
    db: Session = Depends(get_db),
    id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Upload publication document (PDF).
    """
    pub = db.query(Publication).filter(Publication.id == id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
        
    # Access checks: owner, reviewer, or admin
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if pub.created_by != res_id and current_user.role not in [UserRole.system_admin, UserRole.reviewer, UserRole.institution_admin]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to upload files for this publication."
        )
        
    contents = await file.read()
    storage = get_storage()
    file_url = storage.save_file(contents, f"{id}_{file.filename}")
    
    # Update publication file URL
    pub.file_url = file_url
    db.add(pub)
    db.commit()
    db.refresh(pub)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="upload",
        entity_type="publication",
        entity_id=pub.id,
        ip_address=request.client.host if request.client else None,
        details={"filename": file.filename, "file_url": file_url}
    )
    return pub
