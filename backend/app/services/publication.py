from sqlalchemy.orm import Session

from app.models.researcher import Researcher
from app.repositories import publication as publication_repo


def _resolve_authors(db: Session, author_ids: list[int]) -> list[Researcher]:
    if not author_ids:
        return []
    authors = db.query(Researcher).filter(Researcher.id.in_(author_ids)).all()
    found_ids = {a.id for a in authors}
    missing = set(author_ids) - found_ids
    if missing:
        raise ValueError(f"Researcher id(s) not found: {sorted(missing)}")
    return authors


def create_new_publication(db: Session, publication):
    data = publication.model_dump(exclude={"author_ids"})
    authors = _resolve_authors(db, publication.author_ids)
    return publication_repo.create_publication(db, data, authors)


def get_publication_by_id(db: Session, publication_id: int):
    publication = publication_repo.get_publication(db, publication_id)
    if not publication:
        raise ValueError("Publication not found")
    return publication


def list_publications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    publication_type: str | None = None,
    year: int | None = None,
):
    return publication_repo.get_publications(
        db, skip, limit, status, publication_type, year
    )


def list_publications_for_researcher(db: Session, researcher_id: int):
    return publication_repo.get_publications_by_researcher(db, researcher_id)


def update_existing_publication(db: Session, publication_id: int, publication_update):
    update_data = publication_update.model_dump(exclude_unset=True, exclude={"author_ids"})

    authors = None
    if publication_update.author_ids is not None:
        authors = _resolve_authors(db, publication_update.author_ids)

    updated = publication_repo.update_publication(db, publication_id, update_data, authors)
    if not updated:
        raise ValueError("Publication not found")
    return updated


def delete_existing_publication(db: Session, publication_id: int):
    deleted = publication_repo.delete_publication(db, publication_id)
    if not deleted:
        raise ValueError("Publication not found")
    return deleted
