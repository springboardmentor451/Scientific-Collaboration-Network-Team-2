from sqlalchemy.orm import Session

from app.models.publication import Publication
from app.models.researcher import Researcher


def get_publication(db: Session, publication_id: int):
    return db.query(Publication).filter(Publication.id == publication_id).first()


def get_publications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    publication_type: str | None = None,
    year: int | None = None,
):
    query = db.query(Publication)
    if status:
        query = query.filter(Publication.status == status)
    if publication_type:
        query = query.filter(Publication.publication_type == publication_type)
    if year:
        query = query.filter(Publication.year == year)
    return query.offset(skip).limit(limit).all()


def get_publications_by_researcher(db: Session, researcher_id: int):
    return (
        db.query(Publication)
        .join(Publication.authors)
        .filter(Researcher.id == researcher_id)
        .all()
    )


def create_publication(db: Session, data: dict, authors: list[Researcher]):
    db_publication = Publication(**data)
    db_publication.authors = authors
    db.add(db_publication)
    db.commit()
    db.refresh(db_publication)
    return db_publication


def update_publication(
    db: Session, publication_id: int, data: dict, authors: list[Researcher] | None = None
):
    db_publication = get_publication(db, publication_id)
    if not db_publication:
        return None

    for key, value in data.items():
        setattr(db_publication, key, value)

    if authors is not None:
        db_publication.authors = authors

    db.commit()
    db.refresh(db_publication)
    return db_publication


def delete_publication(db: Session, publication_id: int):
    db_publication = get_publication(db, publication_id)
    if not db_publication:
        return None

    db.delete(db_publication)
    db.commit()
    return db_publication
