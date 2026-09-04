from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.users import User
from backend.app.auth.oauth2 import get_current_user
from backend.app.auth.hash import hash_password, verify_password

from pydantic import BaseModel, EmailStr
from typing import Optional


router = APIRouter(
    prefix="/profile",
    tags=["User Profile"]
)


# ============================================================
# SCHEMAS
# ============================================================

class ProfileResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class ProfileAvatarResponse(BaseModel):
    avatar_url: str


# ============================================================
# HELPER
# ============================================================

def get_user_from_token(
    current_user: dict,
    db: Session
):
    user_id = current_user.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token."
        )

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    return user


# ============================================================
# GET CURRENT PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=ProfileResponse
)
def get_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user = get_user_from_token(
        current_user,
        db
    )

    return user


# ============================================================
# UPDATE PROFILE
# ============================================================

@router.put(
    "/me",
    response_model=ProfileResponse
)
def update_profile(
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user = get_user_from_token(
        current_user,
        db
    )

    # --------------------------------------------------------
    # Update name
    # --------------------------------------------------------

    if profile_data.full_name is not None:

        if not profile_data.full_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Full name cannot be empty."
            )

        user.full_name = (
            profile_data.full_name.strip()
        )

    # --------------------------------------------------------
    # Update email
    # --------------------------------------------------------

    if profile_data.email is not None:

        existing_user = (
            db.query(User)
            .filter(
                User.email == profile_data.email,
                User.id != user.id
            )
            .first()
        )

        if existing_user:

            raise HTTPException(
                status_code=400,
                detail="Email already registered."
            )

        user.email = profile_data.email

    db.commit()
    db.refresh(user)

    return user


@router.post("/me/avatar", response_model=ProfileAvatarResponse)
async def upload_avatar(
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = get_user_from_token(current_user, db)
    allowed_types = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    suffix = allowed_types.get(avatar.content_type)
    if not suffix:
        raise HTTPException(status_code=400, detail="Please upload a JPG, PNG, or WebP image.")

    contents = await avatar.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Profile images must be 5 MB or smaller.")

    upload_dir = Path(__file__).resolve().parents[3] / "uploads"
    upload_dir.mkdir(exist_ok=True)
    filename = f"profile_{user.id}{suffix}"
    (upload_dir / filename).write_bytes(contents)
    user.avatar_url = f"/uploads/{filename}"
    db.commit()
    db.refresh(user)
    return {"avatar_url": user.avatar_url}


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.put(
    "/change-password"
)
def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user = get_user_from_token(
        current_user,
        db
    )

    # --------------------------------------------------------
    # Verify current password
    # --------------------------------------------------------

    if not verify_password(
        password_data.current_password,
        user.password_hash
    ):

        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect."
        )

    # --------------------------------------------------------
    # Validate new password
    # --------------------------------------------------------

    if len(password_data.new_password) < 6:

        raise HTTPException(
            status_code=400,
            detail=(
                "New password must contain "
                "at least 6 characters."
            )
        )

    # --------------------------------------------------------
    # Save new password
    # --------------------------------------------------------

    user.password_hash = hash_password(
        password_data.new_password
    )

    db.commit()

    return {
        "message": "Password changed successfully."
    }


# ============================================================
# DELETE MY ACCOUNT
# ============================================================

@router.delete(
    "/me"
)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user = get_user_from_token(
        current_user,
        db
    )

    db.delete(user)
    db.commit()

    return {
        "message": "Account deleted successfully."
    }