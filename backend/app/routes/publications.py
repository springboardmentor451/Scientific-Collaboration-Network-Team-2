from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.publications import Publication
from backend.app.schemas.publication import (
    PublicationCreate,
    PublicationResponse
)


router = APIRouter(
    prefix="/publications",
    tags=["Publications"]
)


# =========================================================
# GET ALL PUBLICATIONS
# =========================================================

@router.get(
    "/",
    response_model=List[PublicationResponse]
)
def get_publications(
    db: Session = Depends(get_db)
):

    publications = (
        db.query(Publication)
        .order_by(Publication.created_at.desc())
        .all()
    )

    return publications


# =========================================================
# GET ONE PUBLICATION
# =========================================================

@router.get(
    "/{publication_id}",
    response_model=PublicationResponse
)
def get_publication(
    publication_id: int,
    db: Session = Depends(get_db)
):

    publication = (
        db.query(Publication)
        .filter(
            Publication.id == publication_id
        )
        .first()
    )

    if not publication:

        raise HTTPException(
            status_code=404,
            detail="Publication not found"
        )

    return publication


# =========================================================
# CREATE PUBLICATION
# =========================================================

@router.post(
    "/",
    response_model=PublicationResponse,
    status_code=201
)
def create_publication(
    publication_data: PublicationCreate,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # Check duplicate DOI
    # -----------------------------------------------------

    if publication_data.doi:

        existing = (
            db.query(Publication)
            .filter(
                Publication.doi ==
                publication_data.doi
            )
            .first()
        )

        if existing:

            raise HTTPException(
                status_code=400,
                detail="A publication with this DOI already exists."
            )


    # -----------------------------------------------------
    # Create publication
    # -----------------------------------------------------

    publication = Publication(
        title=publication_data.title,
        abstract=publication_data.abstract,
        publication_type=publication_data.publication_type,
        journal_name=publication_data.journal_name,
        doi=publication_data.doi,
        publication_date=publication_data.publication_date,
        volume=publication_data.volume,
        issue=publication_data.issue,
        pages=publication_data.pages,
        url=publication_data.url,
        citation_count=publication_data.citation_count
    )


    # -----------------------------------------------------
    # Save to database
    # -----------------------------------------------------

    db.add(publication)

    db.commit()

    db.refresh(publication)

    return publication


# =========================================================
# DELETE PUBLICATION
# =========================================================

@router.delete(
    "/{publication_id}"
)
def delete_publication(
    publication_id: int,
    db: Session = Depends(get_db)
):

    publication = (
        db.query(Publication)
        .filter(
            Publication.id == publication_id
        )
        .first()
    )

    if not publication:

        raise HTTPException(
            status_code=404,
            detail="Publication not found"
        )

    db.delete(publication)

    db.commit()

    return {
        "message": "Publication deleted successfully"
    }