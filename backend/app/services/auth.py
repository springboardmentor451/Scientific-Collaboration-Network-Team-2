from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.repositories import user as user_repo
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate


def register_user(db: Session, user: UserCreate):
    existing = user_repo.get_user_by_email(db, user.email)
    if existing:
        raise ValueError("A user with this email already exists")
    return user_repo.create_user(db, user)


def authenticate_user(db: Session, credentials: LoginRequest):
    user = user_repo.get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise ValueError("Incorrect email or password")
    if not user.is_active:
        raise ValueError("This account has been deactivated")
    return user


def create_token_for_user(user) -> str:
    return create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
