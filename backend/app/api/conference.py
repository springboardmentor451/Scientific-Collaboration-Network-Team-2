from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.conference import (
    ConferenceCreate,
    ConferenceOut,
    ConferenceUpdate,
    ParticipationCreate,
    ParticipationOut,
    ParticipationUpdate,
)
from app.services import conference as conference_service

router = APIRouter(prefix="/conferences", tags=["Conferences"])


@router.post("/", response_model=ConferenceOut)
def create_conference(conference: ConferenceCreate, db: Session = Depends(get_db)):
    return conference_service.create_new_conference(db, conference)


@router.get("/{conference_id}", response_model=ConferenceOut)
def read_conference(conference_id: int, db: Session = Depends(get_db)):
    try:
        return conference_service.get_conference_by_id(db, conference_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=list[ConferenceOut])
def read_conferences(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return conference_service.list_conferences(db, skip, limit)


@router.put("/{conference_id}", response_model=ConferenceOut)
def update_conference(
    conference_id: int, conference: ConferenceUpdate, db: Session = Depends(get_db)
):
    try:
        return conference_service.update_existing_conference(db, conference_id, conference)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{conference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conference(conference_id: int, db: Session = Depends(get_db)):
    try:
        conference_service.delete_existing_conference(db, conference_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/participations", response_model=ParticipationOut)
def create_participation(participation: ParticipationCreate, db: Session = Depends(get_db)):
    try:
        return conference_service.register_participation(db, participation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/participations/all", response_model=list[ParticipationOut])
def read_participations(
    conference_id: int | None = None,
    researcher_id: int | None = None,
    db: Session = Depends(get_db),
):
    return conference_service.list_participations(db, conference_id, researcher_id)


@router.put("/participations/{participation_id}", response_model=ParticipationOut)
def update_participation(
    participation_id: int, participation: ParticipationUpdate, db: Session = Depends(get_db)
):
    try:
        return conference_service.update_existing_participation(
            db, participation_id, participation
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/participations/{participation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participation(participation_id: int, db: Session = Depends(get_db)):
    try:
        conference_service.delete_existing_participation(db, participation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
