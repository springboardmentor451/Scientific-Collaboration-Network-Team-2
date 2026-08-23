from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.publication import PublicationStatus, PublicationType
from app.schemas.publication import PublicationCreate, PublicationOut, PublicationUpdate
from app.services import publication as publication_service

router = APIRouter(prefix="/publications", tags=["Publications"])


@router.post("/", response_model=PublicationOut)
def create_publication(publication: PublicationCreate, db: Session = Depends(get_db)):
    try:
        return publication_service.create_new_publication(db, publication)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{publication_id}", response_model=PublicationOut)
def read_publication(publication_id: int, db: Session = Depends(get_db)):
    try:
        return publication_service.get_publication_by_id(db, publication_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=list[PublicationOut])
def read_publications(
    skip: int = 0,
    limit: int = 100,
    status: PublicationStatus | None = None,
    publication_type: PublicationType | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    return publication_service.list_publications(
        db, skip, limit, status, publication_type, year
    )


@router.get("/researcher/{researcher_id}", response_model=list[PublicationOut])
def read_publications_by_researcher(researcher_id: int, db: Session = Depends(get_db)):
    return publication_service.list_publications_for_researcher(db, researcher_id)


@router.put("/{publication_id}", response_model=PublicationOut)
def update_publication(
    publication_id: int, publication: PublicationUpdate, db: Session = Depends(get_db)
):
    try:
        return publication_service.update_existing_publication(
            db, publication_id, publication
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_publication(publication_id: int, db: Session = Depends(get_db)):
    try:
        publication_service.delete_existing_publication(db, publication_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
