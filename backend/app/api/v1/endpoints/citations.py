from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.researchers import Researcher
from backend.app.models.publications import Publication
from backend.app.models.citations import Citation
from backend.app.schemas.citations import CitationCreate, CitationUpdate, CitationOut
from backend.app.api.deps import get_current_active_user
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/citations/", response_model=List[CitationOut])
def read_citations(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    citing_pub_id: Optional[int] = None,
    cited_pub_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve citation logs list.
    """
    query = db.query(Citation)
    if citing_pub_id:
        query = query.filter(Citation.citing_publication_id == citing_pub_id)
    if cited_pub_id:
        query = query.filter(Citation.cited_publication_id == cited_pub_id)
    return query.offset(skip).limit(limit).all()

@router.get("/citations/{id}", response_model=CitationOut)
def read_citation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get citation record.
    """
    citation = db.query(Citation).filter(Citation.id == id).first()
    if not citation:
        raise HTTPException(status_code=404, detail="Citation record not found")
    return citation

@router.post("/citations/", response_model=CitationOut, status_code=status.HTTP_201_CREATED)
def create_citation(
    *,
    db: Session = Depends(get_db),
    citation_in: CitationCreate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Add a citation entry linking two papers. (Only citing paper owner or admin)
    """
    citing_pub = db.query(Publication).filter(Publication.id == citation_in.citing_publication_id).first()
    if not citing_pub:
        raise HTTPException(status_code=404, detail="Citing publication not found")
        
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if citing_pub.created_by != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=403,
            detail="Only the author of the citing publication or administrators can log citations."
        )
        
    # Check duplicate
    if citation_in.cited_publication_id:
        existing = db.query(Citation).filter(
            Citation.citing_publication_id == citation_in.citing_publication_id,
            Citation.cited_publication_id == citation_in.cited_publication_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="This citation is already logged.")
            
    db_citation = Citation(
        citing_publication_id=citation_in.citing_publication_id,
        cited_publication_id=citation_in.cited_publication_id,
        external_reference_text=citation_in.external_reference_text,
        doi=citation_in.doi
    )
    db.add(db_citation)
    db.commit()
    db.refresh(db_citation)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="log_citation",
        entity_type="citation",
        entity_id=db_citation.id,
        ip_address=request.client.host if request.client else None
    )
    return db_citation

@router.put("/citations/{id}", response_model=CitationOut)
def update_citation(
    *,
    db: Session = Depends(get_db),
    id: int,
    citation_in: CitationUpdate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Update details of a citation log.
    """
    citation = db.query(Citation).filter(Citation.id == id).first()
    if not citation:
        raise HTTPException(status_code=404, detail="Citation record not found")
        
    citing_pub = citation.citing_publication
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if citing_pub.created_by != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=403,
            detail="Only the author of the citing publication or administrators can update citation logs."
        )
        
    update_data = citation_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(citation, field, update_data[field])
        
    db.add(citation)
    db.commit()
    db.refresh(citation)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update_citation",
        entity_type="citation",
        entity_id=citation.id,
        ip_address=request.client.host if request.client else None
    )
    return citation

@router.delete("/citations/{id}")
def delete_citation(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Delete a citation entry.
    """
    citation = db.query(Citation).filter(Citation.id == id).first()
    if not citation:
        raise HTTPException(status_code=404, detail="Citation record not found")
        
    citing_pub = citation.citing_publication
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if citing_pub.created_by != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=403,
            detail="Only the author of the citing publication or administrators can remove citation logs."
        )
        
    db.delete(citation)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete_citation",
        entity_type="citation",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Citation record removed successfully"}
