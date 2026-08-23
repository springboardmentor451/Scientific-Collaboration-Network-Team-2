from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.institution import InstitutionCreate, InstitutionOut, InstitutionUpdate
from app.services import institution as institution_service

institution_router = APIRouter(prefix="/institutions", tags=["Institutions"])


@institution_router.post("/", response_model=InstitutionOut)
def create_institution(institution: InstitutionCreate, db: Session = Depends(get_db)):
    try:
        return institution_service.create_new_institution(db, institution)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@institution_router.get("/{institution_id}", response_model=InstitutionOut)
def read_institution(institution_id: int, db: Session = Depends(get_db)):
    try:
        return institution_service.get_institution_by_id(db, institution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@institution_router.get("/", response_model=list[InstitutionOut])
def read_institutions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return institution_service.list_institutions(db, skip, limit)

@institution_router.put("/{institution_id}", response_model=InstitutionOut)
def update_institution(institution_id: int, institution: InstitutionUpdate, db: Session = Depends(get_db)):
    try:
        return institution_service.update_existing_institution(db, institution_id, institution)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@institution_router.delete("/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_institution(institution_id: int, db: Session = Depends(get_db)):
    try:
        institution_service.delete_existing_institution(db, institution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
