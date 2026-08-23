from sqlalchemy.orm import Session
from app.models.researcher import Researcher
from app.schemas.researcher import ResearcherCreate


def get_researcher(db: Session, researcher_id: int):
    return db.query(Researcher).filter(Researcher.id == researcher_id).first()


def get_researchers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Researcher).offset(skip).limit(limit).all()


def create_researcher(db: Session, researcher: ResearcherCreate):
    db_researcher = Researcher(
        name=researcher.name,
        email=researcher.email,
        department=researcher.department,
        designation=researcher.designation,
    )
    db.add(db_researcher)
    db.commit()
    db.refresh(db_researcher)
    return db_researcher

def get_researcher_by_email(db: Session, email: str):
    return db.query(Researcher).filter(Researcher.email == email).first()

def update_researcher(db: Session, researcher_id: int, data: dict):
    db_researcher = db.query(Researcher).filter(Researcher.id == researcher_id).first()
    if not db_researcher:
        return None

    for key, value in data.items():
        setattr(db_researcher, key, value)

    db.commit()
    db.refresh(db_researcher)
    return db_researcher


def delete_researcher(db: Session, researcher_id: int):
    db_researcher = db.query(Researcher).filter(Researcher.id == researcher_id).first()
    if not db_researcher:
        return None

    db.delete(db_researcher)
    db.commit()
    return db_researcher