from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return auth_service.register_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.authenticate_user(db, credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    token = auth_service.create_token_for_user(user)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user=Depends(get_current_user)):
    return current_user
