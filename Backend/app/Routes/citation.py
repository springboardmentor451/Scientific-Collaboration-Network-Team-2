from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.models.citation import Citation
from app.models.publication import Publication
from app.Schemas.citation import CitationCreate, CitationResponse, CitationUpdate
from app.Crud.audit import log_action

router = APIRouter(prefix="/citations", tags=["Citations & References"])

@router.get("", response_model=list[CitationResponse])
def list_citations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Citation).filter(Citation.owner_id == user.id).order_by(Citation.created_at.desc()).all()

@router.post("", response_model=CitationResponse, status_code=201)
def create_citation(data: CitationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"Researcher", "Faculty", "Publisher", "Admin", "System Admin"}:
        raise HTTPException(403, "Your role cannot create citations.")
    if data.publication_id and not db.query(Publication).filter(Publication.id == data.publication_id, Publication.owner_id == user.id).first():
        raise HTTPException(403, "You can only attach citations to your own publications.")
    item = Citation(**data.model_dump(), owner_id=user.id)
    db.add(item); db.flush(); log_action(db, "CITATION_CREATED", user.id, "Citation", item.id, item.cited_title)
    db.commit(); db.refresh(item); return item

@router.get("/{citation_id}", response_model=CitationResponse)
def get_citation(citation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Citation).filter(Citation.id == citation_id).first()
    if not item: raise HTTPException(404, "Citation not found.")
    if item.owner_id != user.id and user.role not in {"Admin", "System Admin"}: raise HTTPException(403, "You can only view your own citation.")
    return item

@router.put("/{citation_id}", response_model=CitationResponse)
def update_citation(citation_id: int, data: CitationUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Citation).filter(Citation.id == citation_id).first()
    if not item: raise HTTPException(404, "Citation not found.")
    if item.owner_id != user.id and user.role not in {"Admin", "System Admin"}: raise HTTPException(403, "You can only edit your own citation.")
    if data.publication_id and not db.query(Publication).filter(Publication.id == data.publication_id, Publication.owner_id == item.owner_id).first(): raise HTTPException(400, "Linked publication is invalid.")
    for field, value in data.model_dump(exclude_unset=True).items(): setattr(item, field, value)
    log_action(db, "CITATION_UPDATED", user.id, "Citation", item.id, item.cited_title)
    db.commit(); db.refresh(item); return item

@router.delete("/{citation_id}", status_code=204)
def delete_citation(citation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Citation).filter(Citation.id == citation_id).first()
    if not item: raise HTTPException(404, "Citation not found.")
    if item.owner_id != user.id and user.role not in {"Admin", "System Admin"}: raise HTTPException(403, "You can only delete your own citation.")
    log_action(db, "CITATION_DELETED", user.id, "Citation", item.id, item.cited_title)
    db.delete(item); db.commit(); return Response(status_code=204)

@router.get("/admin/all", response_model=list[CitationResponse])
def admin_citations(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return db.query(Citation).order_by(Citation.created_at.desc()).all()
