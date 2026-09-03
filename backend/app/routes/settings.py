from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.users import User
from backend.app.auth.oauth2 import get_current_user

from pydantic import BaseModel
from typing import Optional


router = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)


# ============================================================
# SETTINGS RESPONSE
# ============================================================

class SettingsResponse(BaseModel):

    full_name: str

    email: str

    role: str

    is_active: bool


# ============================================================
# GET SETTINGS
# ============================================================

@router.get(
    "/",
    response_model=SettingsResponse
)
def get_settings(

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    user_id = current_user.get("sub")

    user = (
        db.query(User)
        .filter(
            User.id == int(user_id)
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    return user


# ============================================================
# ACCOUNT STATUS
# ============================================================

@router.get(
    "/account-status"
)
def account_status(

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    user_id = current_user.get("sub")

    user = (
        db.query(User)
        .filter(
            User.id == int(user_id)
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    return {

        "user_id": user.id,

        "email": user.email,

        "role": user.role,

        "is_active": user.is_active,

        "account_created": user.created_at,

        "last_updated": user.updated_at
    }


# ============================================================
# DEACTIVATE MY ACCOUNT
# ============================================================

@router.put(
    "/deactivate"
)
def deactivate_my_account(

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    user_id = current_user.get("sub")

    user = (
        db.query(User)
        .filter(
            User.id == int(user_id)
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    user.is_active = False

    db.commit()

    return {
        "message": "Your account has been deactivated."
    }