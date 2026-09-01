from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.publication import Publication
from app.Schemas.publication import PublicationCreate, PublicationUpdate

def list_publications(db: Session, search=None, owner_id=None, status=None, institution_id=None, skip=0, limit=100):
    query = db.query(Publication)
    if owner_id: query = query.filter(Publication.owner_id == owner_id)
    if status: query = query.filter(Publication.status == status)
    if institution_id:
        from app.models.user import User
        query = query.join(User, Publication.owner_id == User.id).filter(User.institution_id == institution_id)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Publication.title.ilike(pattern), Publication.authors.ilike(pattern), Publication.research_area.ilike(pattern), Publication.venue.ilike(pattern)))
    return query.order_by(Publication.publication_year.desc(), Publication.title).offset(skip).limit(limit).all()

def create_publication(db: Session, data: PublicationCreate, owner_id: int):
    item = Publication(**data.model_dump(), owner_id=owner_id); db.add(item); db.commit(); db.refresh(item); return item

def update_publication(db: Session, item: Publication, data: PublicationUpdate):
    for field, value in data.model_dump(exclude_unset=True).items(): setattr(item, field, value)
    db.commit(); db.refresh(item); return item
