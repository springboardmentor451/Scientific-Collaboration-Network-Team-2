from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Researcher, Tag, TagCategory, User
from app.schemas.common import ResearcherOut
from app.schemas.researcher import ResearcherTagsUpdate, ResearcherUpdate

router = APIRouter(prefix="/researchers", tags=["researchers-write"])

AVATAR_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads" / "avatars"
AVATAR_ROOT.mkdir(parents=True, exist_ok=True)
ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_AVATAR_BYTES = 3 * 1024 * 1024  # 3 MB


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


def _get_or_create_tag(db: Session, name: str, category: TagCategory) -> Tag:
    name = name.strip()
    tag = db.query(Tag).filter(Tag.name == name, Tag.category == category).first()
    if not tag:
        tag = Tag(name=name, category=category)
        db.add(tag)
        db.flush()
    return tag


@router.put("/me/tags", response_model=ResearcherOut)
def update_my_tags(
    payload: ResearcherTagsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Replaces the logged-in researcher's full set of skill/research-interest
    tags with whatever's supplied (find-or-create by name — tags are shared,
    reusable rows, same ones the seed data uses).
    """
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    if not researcher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Researcher profile not found")

    skills = [_get_or_create_tag(db, s, TagCategory.SKILL) for s in payload.skills[:10] if s.strip()]
    interests = [_get_or_create_tag(db, i, TagCategory.RESEARCH_INTEREST) for i in payload.interests[:10] if i.strip()]
    researcher.tags = skills + interests

    db.commit()
    db.refresh(researcher)
    return researcher


@router.post("/me/avatar", response_model=ResearcherOut)
def upload_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Uploads/replaces the logged-in researcher's profile photo (JPG/PNG/WEBP, up to 3MB)."""
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    if not researcher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Researcher profile not found")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image type must be one of: {', '.join(sorted(ALLOWED_AVATAR_EXTENSIONS))}",
        )
    contents = file.file.read()
    if len(contents) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image is larger than the 3MB limit")

    # Fixed filename per researcher (not the original name) so re-uploading
    # just replaces the old photo instead of accumulating orphaned files.
    dest_path = AVATAR_ROOT / f"{researcher.id}{ext}"
    for stale_ext in ALLOWED_AVATAR_EXTENSIONS:
        stale = AVATAR_ROOT / f"{researcher.id}{stale_ext}"
        if stale.exists() and stale != dest_path:
            stale.unlink()
    dest_path.write_bytes(contents)

    researcher.avatar_url = f"/uploads/avatars/{researcher.id}{ext}"
    db.commit()
    db.refresh(researcher)
    return researcher
