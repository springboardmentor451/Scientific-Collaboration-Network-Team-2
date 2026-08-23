from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.researcher import ResearcherCreate, ResearcherOut, ResearcherUpdate
from app.services import researcher as researcher_service

router = APIRouter(prefix="/researchers", tags=["Researchers"])


@router.post("/", response_model=ResearcherOut)
def create_researcher(researcher: ResearcherCreate, db: Session = Depends(get_db)):
    try:
        return researcher_service.create_new_researcher(db, researcher)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{researcher_id}", response_model=ResearcherOut)
def read_researcher(researcher_id: int, db: Session = Depends(get_db)):
    try:
        return researcher_service.get_researcher_by_id(db, researcher_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=list[ResearcherOut])
def read_researchers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return researcher_service.list_researchers(db, skip, limit)

@router.put("/{researcher_id}", response_model=ResearcherOut)
def update_researcher(researcher_id: int, researcher: ResearcherUpdate, db: Session = Depends(get_db)):
    try:
        return researcher_service.update_existing_researcher(db, researcher_id, researcher)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
from fastapi import status

@router.delete("/{researcher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_researcher(researcher_id: int, db: Session = Depends(get_db)):
    try:
        researcher_service.delete_existing_researcher(db, researcher_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
