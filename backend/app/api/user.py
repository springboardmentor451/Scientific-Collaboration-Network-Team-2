from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.database import get_db
from app.models.user import UserRole
from app.schemas.user import UserOut, UserUpdate
from app.services import user as user_service

router = APIRouter(prefix="/users", tags=["User Management"])

admin_only = require_roles(UserRole.SYSTEM_ADMIN)


@router.get("/", response_model=list[UserOut], dependencies=[Depends(admin_only)])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return user_service.list_users(db, skip, limit)


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(admin_only)])
def read_user(user_id: int, db: Session = Depends(get_db)):
    try:
        return user_service.get_user_by_id(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(admin_only)])
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    try:
        return user_service.update_existing_user(db, user_id, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_only)],
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user_service.delete_existing_user(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
