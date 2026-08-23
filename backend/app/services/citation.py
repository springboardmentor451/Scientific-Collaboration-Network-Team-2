from sqlalchemy.orm import Session

from app.repositories import citation as citation_repo
from app.repositories import publication as publication_repo


def create_new_citation(db: Session, citation):
    if not publication_repo.get_publication(db, citation.citing_publication_id):
        raise ValueError("Citing publication not found")
    if citation.cited_publication_id and not publication_repo.get_publication(
        db, citation.cited_publication_id
    ):
        raise ValueError("Cited publication not found")
    return citation_repo.create_citation(db, citation.model_dump())


def update_existing_citation(db: Session, citation_id: int, citation_update):
    update_data = citation_update.model_dump(exclude_unset=True)
    updated = citation_repo.update_citation(db, citation_id, update_data)
    if not updated:
        raise ValueError("Citation not found")
    return updated


def delete_existing_citation(db: Session, citation_id: int):
    deleted = citation_repo.delete_citation(db, citation_id)
    if not deleted:
        raise ValueError("Citation not found")
    return deleted


def get_reference_list(db: Session, publication_id: int):
    """What a publication cites."""
    return citation_repo.get_references_of(db, publication_id)


def get_citation_report(db: Session, publication_id: int):
    """Who cites a publication, and the total citation count (impact)."""
    citing_records = citation_repo.get_citations_of(db, publication_id)
    return {
        "publication_id": publication_id,
        "citation_count": len(citing_records),
        "cited_by": citing_records,
    }
