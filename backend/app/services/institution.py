from sqlalchemy.orm import Session
from app.repositories import institution as institution_repo
from app.schemas.institution import InstitutionCreate


def create_new_institution(db: Session, institution: InstitutionCreate):
    existing = institution_repo.get_institution_by_name(db, institution.name)
    if existing:
        raise ValueError("An Institution with this name already exists")
    return institution_repo.create_institution(db, institution)


def get_institution_by_id(db: Session, institution_id: int):
    institution = institution_repo.get_institution(db, institution_id)
    if not institution:
        raise ValueError("Institution not found")
    return institution


def list_institutions(db: Session, skip: int = 0, limit: int = 100):
    return institution_repo.get_institutions(db, skip, limit)

def update_existing_institution(db: Session, institution_id: int, institution_update):
    update_data = institution_update.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing = institution_repo.get_institution_by_name(db, update_data["name"])
        if existing and existing.id != institution_id:
            raise ValueError("Another institution already uses this name")

    updated = institution_repo.update_institution(db, institution_id, update_data)
    if not updated:
        raise ValueError("Institution not found")
    return updated


def delete_existing_institution(db: Session, institution_id: int):
    deleted = institution_repo.delete_institution(db, institution_id)
    if not deleted:
        raise ValueError("Institution not found")
    return deleted