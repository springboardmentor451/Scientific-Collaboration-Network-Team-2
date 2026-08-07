from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Researcher, User
from app.schemas.common import ResearcherOut
from app.schemas.researcher import ResearcherUpdate

router = APIRouter(prefix="/researchers", tags=["researchers-write"])


@router.put("/me", response_model=ResearcherOut)
def update_my_profile(
    payload: ResearcherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partial update of the logged-in user's own researcher profile.
    Only the fields provided in the request body are changed.
    """
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    if not researcher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Researcher profile not found")

    if payload.orcid_id and payload.orcid_id != researcher.orcid_id:
        clash = db.query(Researcher).filter(Researcher.orcid_id == payload.orcid_id).first()
        if clash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ORCID ID is already in use")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(researcher, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not update profile")

    db.refresh(researcher)
    return researcher
