from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.models.users import User

from backend.app.database.session import get_db
from backend.app.models.researchers import Researcher
from backend.app.schemas.researcher import (
    ResearcherCreate,
    ResearcherUpdate,
    ResearcherResponse
)
from backend.app.auth.oauth2 import get_current_user


router = APIRouter(
    prefix="/researchers",
    tags=["Researchers"]
)


@router.post("/", response_model=ResearcherResponse)
def create_researcher(
    researcher: ResearcherCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))

    # Check whether this user already has a researcher profile
    existing_researcher = (
        db.query(Researcher)
        .filter(Researcher.user_id == user_id)
        .first()
    )

    if existing_researcher:
        raise HTTPException(
            status_code=400,
            detail="Researcher profile already exists"
        )

    new_researcher = Researcher(
        user_id=user_id,
        institution_id=researcher.institution_id,
        research_area=researcher.research_area,
        biography=researcher.biography,
        profile_url=researcher.profile_url
    )

    db.add(new_researcher)
    db.commit()
    db.refresh(new_researcher)

    return new_researcher


@router.get("/me", response_model=ResearcherResponse)
def get_my_researcher_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))

    researcher = (
        db.query(Researcher)
        .filter(Researcher.user_id == user_id)
        .first()
    )

    if not researcher:
        raise HTTPException(
            status_code=404,
            detail="Researcher profile not found"
        )

    return researcher

@router.put("/me", response_model=ResearcherResponse)
def update_my_researcher_profile(
    researcher_data: ResearcherUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))

    researcher = (
        db.query(Researcher)
        .filter(Researcher.user_id == user_id)
        .first()
    )

    if not researcher:
        raise HTTPException(
            status_code=404,
            detail="Researcher profile not found"
        )

    researcher.institution_id = researcher_data.institution_id
    researcher.research_area = researcher_data.research_area
    researcher.biography = researcher_data.biography
    researcher.profile_url = researcher_data.profile_url

    db.commit()
    db.refresh(researcher)

    return researcher

@router.get("/", response_model=list[ResearcherResponse])
def get_all_researchers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    researchers = (
        db.query(Researcher)
        .all()
    )

    result = []

    for researcher in researchers:

        user = (
            db.query(User)
            .filter(User.id == researcher.user_id)
            .first()
        )

        result.append({
            "id": researcher.id,
            "user_id": researcher.user_id,
            "full_name": user.full_name if user else None,
            "email": user.email if user else None,
            "institution_id": researcher.institution_id,
            "research_area": researcher.research_area,
            "biography": researcher.biography,
            "profile_url": researcher.profile_url
        })

    return result