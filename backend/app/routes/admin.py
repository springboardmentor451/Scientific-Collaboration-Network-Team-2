from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.users import User
from backend.app.auth.oauth2 import get_current_user

from pydantic import BaseModel
from typing import Optional


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


# ============================================================
# ADMIN AUTHORIZATION
# ============================================================

def require_admin(
    current_user: dict,
    db: Session
):

    user_id = current_user.get("sub")

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

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

    if user.role.lower() != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admin access required."
        )

    return user


# ============================================================
# ADMIN USER RESPONSE
# ============================================================

class AdminUserResponse(BaseModel):

    id: int
    full_name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================
# ADMIN STATS
# ============================================================

@router.get("/stats")
def get_admin_stats(

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    require_admin(
        current_user,
        db
    )

    total_users = (
        db.query(User)
        .count()
    )

    active_users = (
        db.query(User)
        .filter(
            User.is_active == True
        )
        .count()
    )

    inactive_users = (
        db.query(User)
        .filter(
            User.is_active == False
        )
        .count()
    )

    researchers = (
        db.query(User)
        .filter(
            User.role == "researcher"
        )
        .count()
    )

    admins = (
        db.query(User)
        .filter(
            User.role == "admin"
        )
        .count()
    )

    return {

        "total_users": total_users,

        "active_users": active_users,

        "inactive_users": inactive_users,

        "researchers": researchers,

        "admins": admins
    }


# ============================================================
# GET ALL USERS
# ============================================================

@router.get(
    "/users",
    response_model=list[AdminUserResponse]
)
def get_all_users(

    search: Optional[str] = Query(
        default=None
    ),

    role: Optional[str] = Query(
        default=None
    ),

    status: Optional[str] = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    require_admin(
        current_user,
        db
    )

    query = db.query(User)

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    if search:

        search_value = (
            f"%{search.strip()}%"
        )

        query = query.filter(
            (User.full_name.ilike(search_value))
            |
            (User.email.ilike(search_value))
        )

    # --------------------------------------------------------
    # Role
    # --------------------------------------------------------

    if (
        role
        and role.lower() != "all"
    ):

        query = query.filter(
            User.role == role
        )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if status:

        if status.lower() == "active":

            query = query.filter(
                User.is_active == True
            )

        elif status.lower() == "inactive":

            query = query.filter(
                User.is_active == False
            )

    return (
        query
        .order_by(User.id.desc())
        .all()
    )


# ============================================================
# GET ONE USER
# ============================================================

@router.get(
    "/users/{user_id}",
    response_model=AdminUserResponse
)
def get_user(

    user_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    require_admin(
        current_user,
        db
    )

    user = (
        db.query(User)
        .filter(
            User.id == user_id
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
# ACTIVATE USER
# ============================================================

@router.put(
    "/users/{user_id}/activate"
)
def activate_user(

    user_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    require_admin(
        current_user,
        db
    )

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    user.is_active = True

    db.commit()

    return {
        "message": "User activated successfully."
    }


# ============================================================
# DEACTIVATE USER
# ============================================================

@router.put(
    "/users/{user_id}/deactivate"
)
def deactivate_user(

    user_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    admin = require_admin(
        current_user,
        db
    )

    if admin.id == user_id:

        raise HTTPException(
            status_code=400,
            detail="Admin cannot deactivate themselves."
        )

    user = (
        db.query(User)
        .filter(
            User.id == user_id
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
        "message": "User deactivated successfully."
    }


# ============================================================
# CHANGE USER ROLE
# ============================================================

class RoleUpdate(BaseModel):

    role: str


@router.put(
    "/users/{user_id}/role"
)
def change_user_role(

    user_id: int,

    role_data: RoleUpdate,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    admin = require_admin(
        current_user,
        db
    )

    if admin.id == user_id:

        raise HTTPException(
            status_code=400,
            detail="Admin cannot change their own role."
        )

    allowed_roles = [
        "admin",
        "researcher"
    ]

    if (
        role_data.role.lower()
        not in allowed_roles
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid role. "
                "Use admin or researcher."
            )
        )

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    user.role = (
        role_data.role.lower()
    )

    db.commit()

    return {
        "message": "User role updated successfully.",
        "role": user.role
    }


# ============================================================
# DELETE USER
# ============================================================

@router.delete(
    "/users/{user_id}"
)
def delete_user(

    user_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )
):

    admin = require_admin(
        current_user,
        db
    )

    if admin.id == user_id:

        raise HTTPException(
            status_code=400,
            detail="Admin cannot delete themselves."
        )

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    db.delete(user)

    db.commit()

    return {
        "message": "User deleted successfully."
    }