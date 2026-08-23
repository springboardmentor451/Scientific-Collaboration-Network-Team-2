from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.citation import (
    CitationCreate,
    CitationOut,
    CitationReport,
    CitationUpdate,
)
from app.services import citation as citation_service

router = APIRouter(prefix="/citations", tags=["Citations & References"])


@router.post("/", response_model=CitationOut)
def create_citation(citation: CitationCreate, db: Session = Depends(get_db)):
    try:
        return citation_service.create_new_citation(db, citation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{citation_id}", response_model=CitationOut)
def update_citation(citation_id: int, citation: CitationUpdate, db: Session = Depends(get_db)):
    try:
        return citation_service.update_existing_citation(db, citation_id, citation)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_citation(citation_id: int, db: Session = Depends(get_db)):
    try:
        citation_service.delete_existing_citation(db, citation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/publication/{publication_id}/references", response_model=list[CitationOut])
def read_reference_list(publication_id: int, db: Session = Depends(get_db)):
    """What a given publication cites (its reference list)."""
    return citation_service.get_reference_list(db, publication_id)


@router.get("/publication/{publication_id}/impact", response_model=CitationReport)
def read_citation_report(publication_id: int, db: Session = Depends(get_db)):
    """Who cites a given publication, and how many times (citation count)."""
    return citation_service.get_citation_report(db, publication_id)
