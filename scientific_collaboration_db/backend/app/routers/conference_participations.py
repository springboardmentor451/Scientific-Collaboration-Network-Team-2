from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.deps import get_current_user
from app.database import get_db
from app.models import Conference, ConferenceParticipation, Publication, Researcher, User, UserRole
from app.schemas.common import ParticipationOut
from app.schemas.conference_participation import ParticipationCreate, ParticipationUpdate

router = APIRouter(prefix="/conference-participations", tags=["conference-participations"])


def _get_researcher_or_403(db: Session, current_user: User) -> Researcher:
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only accounts with a researcher profile can do this",
        )
    return researcher


@router.get("", response_model=list[ParticipationOut])
def list_participations(
    conference_id: str | None = None,
    researcher_id: str | None = None,
    db: Session = Depends(get_db),
):
    """List participation records, optionally filtered by conference or researcher."""
    query = db.query(ConferenceParticipation)
    if conference_id:
        query = query.filter(ConferenceParticipation.conference_id == conference_id)
    if researcher_id:
        query = query.filter(ConferenceParticipation.researcher_id == researcher_id)
    return query.order_by(ConferenceParticipation.registered_at.desc()).all()


@router.get("/{participation_id}", response_model=ParticipationOut)
def get_participation(participation_id: str, db: Session = Depends(get_db)):
    participation = db.get(ConferenceParticipation, participation_id)
    if not participation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participation record not found")
    return participation


@router.post("", response_model=ParticipationOut, status_code=status.HTTP_201_CREATED)
def create_participation(
    payload: ParticipationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Registers a researcher's participation in a conference. Defaults to
    registering the submitter themselves; a system admin may register
    someone else by supplying researcher_id explicitly.
    """
    researcher = _get_researcher_or_403(db, current_user)

    target_researcher_id = payload.researcher_id or researcher.id
    if payload.researcher_id and str(payload.researcher_id) != str(researcher.id) and current_user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a system admin can register another researcher for a conference",
        )

    if not db.get(Conference, payload.conference_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="conference_id does not exist")
    if payload.publication_id and not db.get(Publication, payload.publication_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="publication_id does not exist")

    existing = (
        db.query(ConferenceParticipation)
        .filter(
            ConferenceParticipation.conference_id == payload.conference_id,
            ConferenceParticipation.researcher_id == target_researcher_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This researcher is already registered for this conference")

    participation = ConferenceParticipation(
        conference_id=payload.conference_id,
        researcher_id=target_researcher_id,
        publication_id=payload.publication_id,
        role=payload.role,
        presentation_title=payload.presentation_title,
    )
    db.add(participation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create participation record")
    db.refresh(participation)
    log_action(db, current_user.id, "CREATE", "ConferenceParticipation", participation.id, {"conference_id": str(payload.conference_id)})
    return participation


@router.put("/{participation_id}", response_model=ParticipationOut)
def update_participation(
    participation_id: str,
    payload: ParticipationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    participation = db.get(ConferenceParticipation, participation_id)
    if not participation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participation record not found")

    if current_user.role != UserRole.SYSTEM_ADMIN:
        researcher = _get_researcher_or_403(db, current_user)
        if str(participation.researcher_id) != str(researcher.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the researcher themselves or a system admin can edit this participation record",
            )

    if payload.publication_id and not db.get(Publication, payload.publication_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="publication_id does not exist")

    changed = payload.model_dump(exclude_unset=True)
    for field, value in changed.items():
        setattr(participation, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not update participation record")
    db.refresh(participation)
    log_action(db, current_user.id, "UPDATE", "ConferenceParticipation", participation.id, {"fields": list(changed.keys())})
    return participation


@router.delete("/{participation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participation(
    participation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    participation = db.get(ConferenceParticipation, participation_id)
    if not participation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participation record not found")

    if current_user.role != UserRole.SYSTEM_ADMIN:
        researcher = _get_researcher_or_403(db, current_user)
        if str(participation.researcher_id) != str(researcher.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the researcher themselves or a system admin can cancel this participation record",
            )

    db.delete(participation)
    db.commit()
    log_action(db, current_user.id, "DELETE", "ConferenceParticipation", participation_id, {})