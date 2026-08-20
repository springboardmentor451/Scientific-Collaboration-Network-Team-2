from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.researchers import Researcher
from backend.app.models.publications import Publication
from backend.app.models.publication_authors import PublicationAuthor
from backend.app.schemas.publication_authors import PublicationAuthorCreate, PublicationAuthorUpdate, PublicationAuthorOut
from backend.app.api.deps import get_current_active_user
from backend.app.services.audit import create_audit_log

router = APIRouter()

@router.get("/publication-authors/", response_model=List[PublicationAuthorOut])
def read_publication_authors(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    publication_id: int = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve publication author relationships.
    """
    query = db.query(PublicationAuthor)
    if publication_id:
        query = query.filter(PublicationAuthor.publication_id == publication_id)
    return query.offset(skip).limit(limit).all()

@router.get("/publication-authors/{id}", response_model=PublicationAuthorOut)
def read_publication_author(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get author relation by id.
    """
    rel = db.query(PublicationAuthor).filter(PublicationAuthor.id == id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Author relationship not found")
    return rel

@router.post("/publication-authors/", response_model=PublicationAuthorOut, status_code=status.HTTP_201_CREATED)
def create_publication_author(
    *,
    db: Session = Depends(get_db),
    rel_in: PublicationAuthorCreate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Add a co-author relation. (Only publication creator or admin)
    """
    pub = db.query(Publication).filter(Publication.id == rel_in.publication_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
        
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if pub.created_by != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=403,
            detail="Only the publication creator or administrators can add co-authors."
        )
        
    # Check if author relationship already exists
    existing = db.query(PublicationAuthor).filter(
        PublicationAuthor.publication_id == rel_in.publication_id,
        PublicationAuthor.researcher_id == rel_in.researcher_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="This researcher is already associated with this publication.")
        
    db_rel = PublicationAuthor(
        publication_id=rel_in.publication_id,
        researcher_id=rel_in.researcher_id,
        author_order=rel_in.author_order,
        is_corresponding_author=rel_in.is_corresponding_author
    )
    db.add(db_rel)
    db.commit()
    db.refresh(db_rel)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="add_author",
        entity_type="publication_author",
        entity_id=db_rel.id,
        ip_address=request.client.host if request.client else None,
        details={"publication_id": rel_in.publication_id, "researcher_id": rel_in.researcher_id}
    )
    return db_rel

@router.put("/publication-authors/{id}", response_model=PublicationAuthorOut)
def update_publication_author(
    *,
    db: Session = Depends(get_db),
    id: int,
    rel_in: PublicationAuthorUpdate,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Update details of a co-author relation.
    """
    db_rel = db.query(PublicationAuthor).filter(PublicationAuthor.id == id).first()
    if not db_rel:
        raise HTTPException(status_code=404, detail="Author relationship not found")
        
    pub = db_rel.publication
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if pub.created_by != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=403,
            detail="Only the publication creator or administrators can modify co-author details."
        )
        
    update_data = rel_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(db_rel, field, update_data[field])
        
    db.add(db_rel)
    db.commit()
    db.refresh(db_rel)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update_author",
        entity_type="publication_author",
        entity_id=db_rel.id,
        ip_address=request.client.host if request.client else None
    )
    return db_rel

@router.delete("/publication-authors/{id}")
def delete_publication_author(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Remove a co-author relation.
    """
    db_rel = db.query(PublicationAuthor).filter(PublicationAuthor.id == id).first()
    if not db_rel:
        raise HTTPException(status_code=404, detail="Author relationship not found")
        
    pub = db_rel.publication
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    res_id = researcher.id if researcher else -1
    
    if pub.created_by != res_id and current_user.role != UserRole.system_admin:
        raise HTTPException(
            status_code=403,
            detail="Only the publication creator or administrators can remove co-authors."
        )
        
    db.delete(db_rel)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="remove_author",
        entity_type="publication_author",
        entity_id=id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Author relationship removed successfully"}
