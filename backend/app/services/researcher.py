from sqlalchemy.orm import Session
from app.repositories import researcher as researcher_repo
from app.schemas.researcher import ResearcherCreate


def create_new_researcher(db: Session, researcher: ResearcherCreate):
    existing = researcher_repo.get_researcher_by_email(db, researcher.email)
    if existing:
        raise ValueError("A researcher with this email already exists")
    return researcher_repo.create_researcher(db, researcher)


def get_researcher_by_id(db: Session, researcher_id: int):
    researcher = researcher_repo.get_researcher(db, researcher_id)
    if not researcher:
        raise ValueError("Researcher not found")
    return researcher


def list_researchers(db: Session, skip: int = 0, limit: int = 100):
    return researcher_repo.get_researchers(db, skip, limit)

def update_existing_researcher(db: Session, researcher_id: int, researcher_update):
    update_data = researcher_update.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing = researcher_repo.get_researcher_by_email(db, update_data["email"])
        if existing and existing.id != researcher_id:
            raise ValueError("Another researcher already uses this email")

    updated = researcher_repo.update_researcher(db, researcher_id, update_data)
    if not updated:
        raise ValueError("Researcher not found")
    return updated


def delete_existing_researcher(db: Session, researcher_id: int):
    deleted = researcher_repo.delete_researcher(db, researcher_id)
    if not deleted:
        raise ValueError("Researcher not found")
    return deleted