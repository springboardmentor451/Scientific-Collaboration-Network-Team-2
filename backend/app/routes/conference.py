from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.auth.oauth2 import get_current_user
from backend.app.database.session import get_db

from backend.app.models.conferences import Conference
from backend.app.models.conference_participants import ConferenceParticipant
from backend.app.models.researchers import Researcher

from backend.app.schemas.conference import (
    ConferenceCreate,
    ConferenceUpdate,
    ConferenceResponse,
    ConferenceParticipantCreate,
    ConferenceParticipantResponse,
    ConferenceStatsResponse,
)


router = APIRouter(
    prefix="/conferences",
    tags=["Conferences"]
)


# ============================================================
# VALIDATION
# ============================================================

def validate_dates(start_date, end_date):

    if (
        start_date
        and end_date
        and end_date < start_date
    ):
        raise HTTPException(
            status_code=400,
            detail="End date cannot be earlier than start date."
        )


def validate_researcher(
    db: Session,
    researcher_id: int
):

    researcher = (
        db.query(Researcher)
        .filter(
            Researcher.id == researcher_id
        )
        .first()
    )

    if not researcher:
        raise HTTPException(
            status_code=404,
            detail=f"Researcher {researcher_id} not found."
        )

    return researcher


# ============================================================
# CONFERENCE STATISTICS
# ============================================================

@router.get(
    "/stats",
    response_model=ConferenceStatsResponse
)
def get_conference_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    conferences = (
        db.query(Conference)
        .all()
    )

    today = date.today()

    upcoming = 0
    completed = 0
    cancelled = 0
    total_participants = 0

    for conference in conferences:

        status = conference.status.lower()

        if status == "upcoming":
            upcoming += 1

        elif status == "completed":
            completed += 1

        elif status == "cancelled":
            cancelled += 1

        # Count actual participants
        participant_count = (
            db.query(ConferenceParticipant)
            .filter(
                ConferenceParticipant.conference_id
                == conference.id
            )
            .count()
        )

        total_participants += participant_count

    return {
        "total_conferences": len(conferences),
        "upcoming": upcoming,
        "completed": completed,
        "cancelled": cancelled,
        "total_participants": total_participants
    }


# ============================================================
# GET ALL CONFERENCES
# ============================================================

@router.get(
    "/",
    response_model=list[ConferenceResponse]
)
def get_conferences(

    search: str | None = Query(
        default=None
    ),

    field: str | None = Query(
        default=None
    ),

    status: str | None = Query(
        default=None
    ),

    sort: str = Query(
        default="date_desc"
    ),

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    query = db.query(
        Conference
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        search_text = (
            f"%{search.strip()}%"
        )

        query = query.filter(
            Conference.name.ilike(
                search_text
            )
            |
            Conference.description.ilike(
                search_text
            )
            |
            Conference.location.ilike(
                search_text
            )
            |
            Conference.organizer.ilike(
                search_text
            )
            |
            Conference.field.ilike(
                search_text
            )
        )

    # --------------------------------------------------------
    # FIELD FILTER
    # --------------------------------------------------------

    if (
        field
        and field.lower() != "all"
    ):

        query = query.filter(
            Conference.field == field
        )

    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    if sort == "date_asc":

        query = query.order_by(
            Conference.start_date.asc().nullslast()
        )

    elif sort == "name_asc":

        query = query.order_by(
            Conference.name.asc()
        )

    elif sort == "name_desc":

        query = query.order_by(
            Conference.name.desc()
        )

    elif sort == "date_desc":

        query = query.order_by(
            Conference.start_date.desc().nullslast(),
            Conference.id.desc()
        )

    else:

        query = query.order_by(
            Conference.start_date.desc().nullslast(),
            Conference.id.desc()
        )

    conferences = query.all()

    if status and status.lower() != "all":
        requested_status = status.strip().lower()
        conferences = [
            conference
            for conference in conferences
            if conference.status.lower() == requested_status
        ]

    return conferences


# ============================================================
# GET SINGLE CONFERENCE
# ============================================================

@router.get(
    "/{conference_id}",
    response_model=ConferenceResponse
)
def get_conference(

    conference_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    conference = (
        db.query(Conference)
        .filter(
            Conference.id == conference_id
        )
        .first()
    )

    if not conference:

        raise HTTPException(
            status_code=404,
            detail="Conference not found."
        )

    return conference


# ============================================================
# CREATE CONFERENCE
# ============================================================

@router.post(
    "/",
    response_model=ConferenceResponse,
    status_code=201
)
def create_conference(

    conference_data: ConferenceCreate,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    validate_dates(
        conference_data.start_date,
        conference_data.end_date
    )

    conference = Conference(

        name=conference_data.name.strip(),

        description=conference_data.description,

        organizer=conference_data.organizer,

        location=conference_data.location,

        start_date=conference_data.start_date,

        end_date=conference_data.end_date,

        field=conference_data.field,

        website=(
            str(conference_data.website)
            if conference_data.website
            else None
        )
    )

    db.add(conference)

    db.commit()

    db.refresh(conference)

    return conference


# ============================================================
# UPDATE CONFERENCE
# ============================================================

@router.put(
    "/{conference_id}",
    response_model=ConferenceResponse
)
def update_conference(

    conference_id: int,

    conference_data: ConferenceUpdate,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    conference = (
        db.query(Conference)
        .filter(
            Conference.id == conference_id
        )
        .first()
    )

    if not conference:

        raise HTTPException(
            status_code=404,
            detail="Conference not found."
        )

    values = conference_data.model_dump(
        exclude_unset=True
    )

    new_start = values.get(
        "start_date",
        conference.start_date
    )

    new_end = values.get(
        "end_date",
        conference.end_date
    )

    validate_dates(
        new_start,
        new_end
    )

    # Convert HttpUrl to string
    if (
        "website" in values
        and values["website"]
    ):

        values["website"] = str(
            values["website"]
        )

    # Trim name
    if (
        "name" in values
        and values["name"]
    ):

        values["name"] = (
            values["name"].strip()
        )

    for key, value in values.items():

        setattr(
            conference,
            key,
            value
        )

    db.commit()

    db.refresh(conference)

    return conference


# ============================================================
# DELETE CONFERENCE
# ============================================================

@router.delete(
    "/{conference_id}",
    status_code=204
)
def delete_conference(

    conference_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    conference = (
        db.query(Conference)
        .filter(
            Conference.id == conference_id
        )
        .first()
    )

    if not conference:

        raise HTTPException(
            status_code=404,
            detail="Conference not found."
        )

    db.delete(conference)

    db.commit()

    return None


# ============================================================
# ADD PARTICIPANT
# ============================================================

@router.post(
    "/{conference_id}/participants",
    response_model=ConferenceParticipantResponse,
    status_code=201
)
def add_conference_participant(

    conference_id: int,

    participant_data:
        ConferenceParticipantCreate,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    # --------------------------------------------------------
    # Check conference
    # --------------------------------------------------------

    conference = (
        db.query(Conference)
        .filter(
            Conference.id == conference_id
        )
        .first()
    )

    if not conference:

        raise HTTPException(
            status_code=404,
            detail="Conference not found."
        )

    # --------------------------------------------------------
    # Check researcher
    # --------------------------------------------------------

    validate_researcher(
        db,
        participant_data.researcher_id
    )

    # --------------------------------------------------------
    # Prevent duplicate registration
    # --------------------------------------------------------

    existing = (
        db.query(
            ConferenceParticipant
        )
        .filter(
            ConferenceParticipant.conference_id
            == conference_id,

            ConferenceParticipant.researcher_id
            == participant_data.researcher_id
        )
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail=(
                "Researcher is already "
                "registered for this conference."
            )
        )

    # --------------------------------------------------------
    # Create participant
    # --------------------------------------------------------

    participant = ConferenceParticipant(

        conference_id=conference_id,

        researcher_id=(
            participant_data.researcher_id
        ),

        role=participant_data.role,

        registration_status=(
            participant_data.registration_status
        ),

        attended=(
            participant_data.attended
        )
    )

    db.add(participant)

    db.commit()

    db.refresh(participant)

    return participant


# ============================================================
# GET CONFERENCE PARTICIPANTS
# ============================================================

@router.get(
    "/{conference_id}/participants",
    response_model=list[ConferenceParticipantResponse]
)
def get_conference_participants(

    conference_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    conference = (
        db.query(Conference)
        .filter(
            Conference.id == conference_id
        )
        .first()
    )

    if not conference:

        raise HTTPException(
            status_code=404,
            detail="Conference not found."
        )

    participants = (
        db.query(
            ConferenceParticipant
        )
        .filter(
            ConferenceParticipant.conference_id
            == conference_id
        )
        .all()
    )

    return participants


# ============================================================
# REMOVE PARTICIPANT
# ============================================================

@router.delete(
    "/{conference_id}/participants/{researcher_id}",
    status_code=204
)
def remove_conference_participant(

    conference_id: int,

    researcher_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    participant = (
        db.query(
            ConferenceParticipant
        )
        .filter(
            ConferenceParticipant.conference_id
            == conference_id,

            ConferenceParticipant.researcher_id
            == researcher_id
        )
        .first()
    )

    if not participant:

        raise HTTPException(
            status_code=404,
            detail="Conference participant not found."
        )

    db.delete(participant)

    db.commit()

    return None