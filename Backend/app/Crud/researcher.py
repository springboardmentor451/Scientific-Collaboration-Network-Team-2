from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.Schemas.researcher import ResearcherCreate, ResearcherUpdate
from app.models.researcher import Researcher


def get_researcher(db: Session, researcher_id: int):
    return db.query(Researcher).filter(Researcher.id == researcher_id).first()


def get_researcher_by_email(db: Session, email: str):
    return db.query(Researcher).filter(func.lower(Researcher.email) == email.lower()).first()


def get_researchers(db: Session, search: str | None = None, skip: int = 0, limit: int = 100):
    query = db.query(Researcher)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Researcher.name.ilike(pattern),
                Researcher.email.ilike(pattern),
                Researcher.department.ilike(pattern),
                Researcher.institution.ilike(pattern),
                Researcher.field.ilike(pattern),
                Researcher.affiliation.ilike(pattern),
            )
        )
    return query.order_by(Researcher.name).offset(skip).limit(limit).all()


def create_researcher(db: Session, researcher: ResearcherCreate, user_id: int, institution_id: int | None = None):
    db_researcher = Researcher(**researcher.model_dump(), user_id=user_id, institution_id=institution_id)
    db.add(db_researcher)
    db.commit()
    db.refresh(db_researcher)
    return db_researcher


def update_researcher(db: Session, db_researcher: Researcher, researcher: ResearcherUpdate):
    for field, value in researcher.model_dump(exclude_unset=True).items():
        setattr(db_researcher, field, value)
    db.commit()
    db.refresh(db_researcher)
    return db_researcher


def delete_researcher(db: Session, db_researcher: Researcher):
    db.delete(db_researcher)
    db.commit()
