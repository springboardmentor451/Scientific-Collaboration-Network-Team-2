from sqlalchemy.orm import Session
from app.models.institution import Institution
from app.schemas.institution import InstitutionCreate


def get_institution(db: Session, institution_id: int):
    return db.query(Institution).filter(Institution.id == institution_id).first()


def get_institutions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Institution).offset(skip).limit(limit).all()


def create_institution(db: Session, institution: InstitutionCreate):
    db_institution = Institution(**institution.model_dump())
    db.add(db_institution)
    db.commit()
    db.refresh(db_institution)
    return db_institution

def get_institution_by_name(db: Session, name: str):
    return db.query(Institution).filter(Institution.name == name).first()

def update_institution(db: Session, institution_id: int, data: dict):
    db_institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not db_institution:
        return None

    for key, value in data.items():
        setattr(db_institution, key, value)

    db.commit()
    db.refresh(db_institution)
    return db_institution


def delete_institution(db: Session, institution_id: int):
    db_institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not db_institution:
        return None

    db.delete(db_institution)
    db.commit()
    return db_institution