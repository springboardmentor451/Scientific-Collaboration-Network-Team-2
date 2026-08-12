from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.researchers import Researcher
from backend.app.schemas.researcher import (
    ResearcherCreate,
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