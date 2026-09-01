from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.publication import Publication
from app.models.researcher import Researcher
from app.models.review import Review
from app.Schemas.publication import PublicationCreate, PublicationResponse, PublicationUpdate
from app.Crud import publication as crud
from app.Crud.audit import log_action

router = APIRouter(prefix="/publications", tags=["Publications"])
UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads" / "publications"

def response(item: Publication):
    return {**{field: getattr(item, field) for field in ("id", "owner_id", "title", "authors", "abstract", "research_area", "venue", "publication_year", "doi_url", "publication_type", "status", "document_path")}, "owner_name": item.owner_name, "researcher_author_ids": [author.id for author in item.researcher_authors]}

@router.get("", response_model=list[PublicationResponse])
def get_publications(search: str | None = Query(default=None), mine: bool = False, status_filter: str | None = Query(default=None, alias="status"), institution_id: int | None = None, skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == "Institution Admin": institution_id = user.institution_id
    if user.role == "Reviewer":
        assigned_ids = db.query(Review.publication_id).filter(Review.reviewer_id == user.id)
        query = db.query(Publication).filter(Publication.id.in_(assigned_ids))
        if search:
            pattern = f"%{search}%"
            query = query.filter(Publication.title.ilike(pattern) | Publication.authors.ilike(pattern) | Publication.research_area.ilike(pattern) | Publication.venue.ilike(pattern))
        return [response(item) for item in query.order_by(Publication.publication_year.desc(), Publication.title).offset(skip).limit(limit).all()]
    return [response(item) for item in crud.list_publications(db, search, user.id if mine else None, status_filter, institution_id, skip, limit)]

@router.post("", response_model=PublicationResponse, status_code=201)
def add_publication(data: PublicationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"Researcher", "Faculty", "Publisher", "Admin", "System Admin"}: raise HTTPException(403, "Your role cannot add publications.")
    item = crud.create_publication(db, data, user.id); log_action(db, "PUBLICATION_CREATED", user.id, "Publication", item.id, item.title); db.commit(); return response(item)

def owned(publication_id, db, user):
    item = db.query(Publication).filter(Publication.id == publication_id).first()
    if not item: raise HTTPException(404, "Publication not found.")
    if user.role == "Reviewer":
        raise HTTPException(403, "Reviewers cannot modify publication records.")
    is_institution_manager = user.role == "Institution Admin" and item.owner and item.owner.institution_id == user.institution_id
    if item.owner_id != user.id and user.role not in {"Admin", "System Admin"} and not is_institution_manager:
        raise HTTPException(403, "You can only modify publications you own or manage for your institution.")
    return item

@router.get("/{publication_id}", response_model=PublicationResponse)
def get_publication(publication_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Publication).filter(Publication.id == publication_id).first()
    if not item: raise HTTPException(404, "Publication not found.")
    if user.role == "Institution Admin" and (not item.owner or item.owner.institution_id != user.institution_id):
        raise HTTPException(403, "You can only view publications from your institution.")
    return item

@router.put("/{publication_id}", response_model=PublicationResponse)
def edit_publication(publication_id: int, data: PublicationUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = crud.update_publication(db, owned(publication_id, db, user), data); log_action(db, "PUBLICATION_UPDATED", user.id, "Publication", item.id, item.title); db.commit(); return response(item)

@router.post("/{publication_id}/authors/{researcher_id}", response_model=PublicationResponse)
def assign_author(publication_id:int, researcher_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    item=owned(publication_id,db,user); researcher=db.query(Researcher).filter(Researcher.id==researcher_id).first()
    if not researcher: raise HTTPException(404,"Researcher not found.")
    if researcher not in item.researcher_authors: item.researcher_authors.append(researcher)
    log_action(db,"PUBLICATION_AUTHOR_ASSIGNED",user.id,"Publication",item.id,researcher.name);db.commit();db.refresh(item);return response(item)

@router.delete("/{publication_id}/authors/{researcher_id}", response_model=PublicationResponse)
def remove_author(publication_id:int, researcher_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    item=owned(publication_id,db,user); researcher=db.query(Researcher).filter(Researcher.id==researcher_id).first()
    if not researcher: raise HTTPException(404,"Researcher not found.")
    if researcher in item.researcher_authors: item.researcher_authors.remove(researcher)
    log_action(db,"PUBLICATION_AUTHOR_REMOVED",user.id,"Publication",item.id,researcher.name);db.commit();db.refresh(item);return response(item)

@router.delete("/{publication_id}", status_code=204)
def remove_publication(publication_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = owned(publication_id, db, user); log_action(db, "PUBLICATION_DELETED", user.id, "Publication", item.id, item.title); db.delete(item); db.commit(); return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{publication_id}/upload", response_model=PublicationResponse)
async def upload_document(publication_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = owned(publication_id, db, user)
    if not file.filename or not file.filename.lower().endswith(".pdf"): raise HTTPException(400, "Only PDF publication documents are supported.")
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    file_name = f"{publication_id}-{uuid4().hex}.pdf"
    target = UPLOAD_ROOT / file_name
    content = await file.read()
    if len(content) > 15 * 1024 * 1024: raise HTTPException(400, "PDF must be 15 MB or smaller.")
    target.write_bytes(content)
    item.document_path = file_name; log_action(db, "PUBLICATION_DOCUMENT_UPLOADED", user.id, "Publication", item.id, file.filename); db.commit(); db.refresh(item)
    return response(item)

@router.get("/{publication_id}/document")
def view_document(publication_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Publication).filter(Publication.id == publication_id).first()
    if not item: raise HTTPException(404, "Publication not found.")
    if user.role == "Reviewer" and not db.query(Review).filter(Review.publication_id == item.id, Review.reviewer_id == user.id).first():
        raise HTTPException(403, "You can only view documents assigned for your review.")
    if not item.document_path: raise HTTPException(404, "No document uploaded for this publication.")
    target = UPLOAD_ROOT / item.document_path
    if not target.is_file(): raise HTTPException(404, "Publication document is unavailable.")
    return FileResponse(target, media_type="application/pdf", filename=f"publication-{item.id}.pdf")
