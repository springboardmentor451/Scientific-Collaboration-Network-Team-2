from fastapi import APIRouter, Depends, HTTPException
import pycountry
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from backend.app.database.session import get_db

from backend.app.models.researchers import Researcher
from backend.app.models.users import User
from backend.app.auth.hash import hash_password
from backend.app.models.institutions import Institution
from backend.app.models.publications import Publication
from backend.app.models.publication_authors import PublicationAuthor
from backend.app.models.collaborations import Collaboration

from backend.app.schemas.researcher import (
    ResearcherCreate,
    ResearcherUpdate,
    ResearcherResponse,
    ResearcherAdminCreate
)

from backend.app.auth.oauth2 import get_current_user


router = APIRouter(
    prefix="/researchers",
    tags=["Researchers"]
)


# ============================================================
# HELPER: CALCULATE H-INDEX
# ============================================================

def calculate_h_index(citation_counts):

    if not citation_counts:
        return 0

    # Highest citation count first
    citation_counts.sort(reverse=True)

    h_index = 0

    for position, citations in enumerate(
        citation_counts,
        start=1
    ):

        if citations >= position:
            h_index = position

        else:
            break

    return h_index


# ============================================================
# CREATE RESEARCHER
# ============================================================

@router.post(
    "/",
    response_model=ResearcherResponse
)
def create_researcher(
    researcher: ResearcherCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user_id = int(
        current_user.get("sub")
    )

    existing_researcher = (
        db.query(Researcher)
        .filter(
            Researcher.user_id == user_id
        )
        .first()
    )

    if existing_researcher:

        raise HTTPException(
            status_code=400,
            detail="Researcher profile already exists"
        )

    new_researcher = Researcher(

        user_id=user_id,

        institution_id=
            researcher.institution_id,

        research_area=
            researcher.research_area,

        biography=
            researcher.biography,

        profile_url=
            researcher.profile_url,

        status=
            researcher.status or "Active"
    )

    db.add(new_researcher)

    db.commit()

    db.refresh(new_researcher)

    return get_researcher_data(
        new_researcher,
        db
    )
@router.post("/admin", response_model=ResearcherResponse)
def create_researcher_by_admin(
    researcher_data: ResearcherAdminCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # ----------------------------------------
    # Check whether email already exists
    # ----------------------------------------

    existing_user = (
        db.query(User)
        .filter(User.email == researcher_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # ----------------------------------------
    # Check institution if supplied
    # ----------------------------------------

    institution = None

    if researcher_data.institution_id is not None:

        institution = (
            db.query(Institution)
            .filter(
                Institution.id ==
                researcher_data.institution_id
            )
            .first()
        )

        if not institution:
            raise HTTPException(
                status_code=400,
                detail="Selected institution does not exist"
            )

    # ----------------------------------------
    # Create User
    # ----------------------------------------

    hashed_password = hash_password(
        researcher_data.password
    )

    new_user = User(
        full_name=researcher_data.full_name,
        email=researcher_data.email,
        password_hash=hashed_password,
        role="researcher",
        is_active=True
    )

    db.add(new_user)
    db.flush()

    # ----------------------------------------
    # Create Researcher
    # ----------------------------------------

    new_researcher = Researcher(
        user_id=new_user.id,
        institution_id=researcher_data.institution_id,
        research_area=researcher_data.research_area,
        biography=researcher_data.biography,
        profile_url=researcher_data.profile_url,
        status=researcher_data.status
    )

    db.add(new_researcher)

    db.commit()

    db.refresh(new_user)
    db.refresh(new_researcher)

    # ----------------------------------------
    # Return combined data
    # ----------------------------------------

    institution_name = None
    country = None

    if institution:

        institution_name = institution.name
        country = institution.country

    return {
        "id": new_researcher.id,
        "user_id": new_user.id,

        "full_name": new_user.full_name,
        "email": new_user.email,

        "institution_id": new_researcher.institution_id,
        "institution_name": institution_name,
        "country": country,

        "research_area": new_researcher.research_area,
        "biography": new_researcher.biography,
        "profile_url": new_researcher.profile_url,

        "h_index": 0,
        "papers": 0,
        "citations": 0,
        "collaborators": 0,

        "status": new_researcher.status
    }


# ============================================================
# GET MY RESEARCHER PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=ResearcherResponse
)
def get_my_researcher_profile(

    db: Session = Depends(get_db),

    current_user: dict =
        Depends(get_current_user)
):

    user_id = int(
        current_user.get("sub")
    )

    researcher = (
        db.query(Researcher)
        .filter(
            Researcher.user_id == user_id
        )
        .first()
    )

    if not researcher:

        raise HTTPException(
            status_code=404,
            detail="Researcher profile not found"
        )

    return get_researcher_data(
        researcher,
        db
    )


# ============================================================
# UPDATE MY RESEARCHER PROFILE
# ============================================================

@router.put(
    "/me",
    response_model=ResearcherResponse
)
def update_my_researcher_profile(

    researcher_data: ResearcherUpdate,

    db: Session =
        Depends(get_db),

    current_user: dict =
        Depends(get_current_user)
):

    user_id = int(
        current_user.get("sub")
    )

    researcher = (
        db.query(Researcher)
        .filter(
            Researcher.user_id == user_id
        )
        .first()
    )

    if not researcher:

        raise HTTPException(
            status_code=404,
            detail="Researcher profile not found"
        )

    researcher.institution_id = (
        researcher_data.institution_id
    )

    researcher.research_area = (
        researcher_data.research_area
    )

    researcher.biography = (
        researcher_data.biography
    )

    researcher.profile_url = (
        researcher_data.profile_url
    )

    researcher.status = (
        researcher_data.status or "Active"
    )

    db.commit()

    db.refresh(researcher)

    return get_researcher_data(
        researcher,
        db
    )


# ============================================================
# GET ALL RESEARCHERS
# ============================================================

@router.get("/countries")
def get_researcher_countries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    database_countries = {
        country.strip()
        for country, in db.query(Institution.country)
        .filter(Institution.country.isnot(None))
        .all()
        if country and country.strip()
    }
    all_countries = {
        country.name
        for country in pycountry.countries
    }

    return sorted(all_countries | database_countries)

@router.get("/institutions")
def get_researcher_institutions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return [
        {
            "id": institution.id,
            "name": institution.name,
            "country": institution.country
        }
        for institution in db.query(Institution)
        .order_by(Institution.name.asc())
        .all()
    ]

@router.get(
    "/",
    response_model=list[ResearcherResponse]
)
def get_all_researchers(

    db: Session =
        Depends(get_db),

    current_user: dict =
        Depends(get_current_user)
):

    researchers = (
        db.query(Researcher)
        .all()
    )

    result = []

    for researcher in researchers:

        result.append(
            get_researcher_data(
                researcher,
                db
            )
        )

    return result


# ============================================================
# BUILD COMPLETE RESEARCHER RESPONSE
# ============================================================

def get_researcher_data(
    researcher,
    db
):

    # --------------------------------------------------------
    # USER INFORMATION
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(
            User.id == researcher.user_id
        )
        .first()
    )


    full_name = (
        user.full_name
        if user
        else None
    )


    email = (
        user.email
        if user
        else None
    )


    # --------------------------------------------------------
    # INSTITUTION INFORMATION
    # --------------------------------------------------------

    institution = None

    if researcher.institution_id:

        institution = (
            db.query(Institution)
            .filter(
                Institution.id ==
                researcher.institution_id
            )
            .first()
        )


    institution_name = (
        institution.name
        if institution
        else None
    )


    country = (
        institution.country
        if institution
        else None
    )


    # --------------------------------------------------------
    # PUBLICATIONS
    # --------------------------------------------------------

    publication_records = (

        db.query(
            Publication
        )

        .join(
            PublicationAuthor,

            Publication.id ==
            PublicationAuthor.publication_id
        )

        .filter(
            PublicationAuthor.researcher_id ==
            researcher.id
        )

        .all()
    )


    # Number of papers

    papers = len(
        publication_records
    )


    # Citation counts

    citation_counts = [

        publication.citation_count or 0

        for publication
        in publication_records
    ]


    # Total citations

    citations = sum(
        citation_counts
    )


    # H-index

    h_index = calculate_h_index(
        citation_counts
    )


    # --------------------------------------------------------
    # COLLABORATORS
    # --------------------------------------------------------

    collaborations = (

        db.query(
            Collaboration
        )

        .filter(

            or_(

                Collaboration.researcher_id_1 ==
                researcher.id,

                Collaboration.researcher_id_2 ==
                researcher.id

            )

        )

        .all()
    )


    collaborator_ids = set()


    for collaboration in collaborations:

        if (
            collaboration.researcher_id_1
            == researcher.id
        ):

            collaborator_ids.add(
                collaboration.researcher_id_2
            )

        else:

            collaborator_ids.add(
                collaboration.researcher_id_1
            )


    collaborators = len(
        collaborator_ids
    )


    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {

        "id":
            researcher.id,

        "user_id":
            researcher.user_id,

        "full_name":
            full_name,

        "email":
            email,

        "institution_id":
            researcher.institution_id,

        "institution_name":
            institution_name,

        "country":
            country,

        "research_area":
            researcher.research_area,

        "biography":
            researcher.biography,

        "profile_url":
            researcher.profile_url,

        "h_index":
            h_index,

        "papers":
            papers,

        "citations":
            citations,

        "collaborators":
            collaborators,

        "status":
            researcher.status
    }