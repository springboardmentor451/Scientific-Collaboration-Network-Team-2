from sqlalchemy.orm import Session

from app.models.citation import Citation


def get_citation(db: Session, citation_id: int):
    return db.query(Citation).filter(Citation.id == citation_id).first()


def create_citation(db: Session, data: dict):
    db_citation = Citation(**data)
    db.add(db_citation)
    db.commit()
    db.refresh(db_citation)
    return db_citation


def update_citation(db: Session, citation_id: int, data: dict):
    db_citation = get_citation(db, citation_id)
    if not db_citation:
        return None
    for key, value in data.items():
        setattr(db_citation, key, value)
    db.commit()
    db.refresh(db_citation)
    return db_citation


def delete_citation(db: Session, citation_id: int):
    db_citation = get_citation(db, citation_id)
    if not db_citation:
        return None
    db.delete(db_citation)
    db.commit()
    return db_citation


def get_references_of(db: Session, publication_id: int):
    """All works a given publication cites."""
    return db.query(Citation).filter(Citation.citing_publication_id == publication_id).all()


def get_citations_of(db: Session, publication_id: int):
    """All in-system publications that cite a given publication."""
    return db.query(Citation).filter(Citation.cited_publication_id == publication_id).all()


def count_citations_of(db: Session, publication_id: int) -> int:
    return (
        db.query(Citation).filter(Citation.cited_publication_id == publication_id).count()
    )
