import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from backend.app.core import security
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.schemas.users import (
    UserCreate, UserOut, Token, TokenPayload,
    VerifyEmailToken, ResendVerification, PasswordChange
)
from backend.app.services.audit import create_audit_log
from backend.app.api.deps import get_current_active_user

router = APIRouter()

@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    request: Request
) -> Any:
    """
    Register a new user.
    """
    normalized_email = user_in.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    db_user = User(
        email=normalized_email,
        password_hash=security.get_password_hash(user_in.password),
        role=user_in.role or UserRole.researcher,
        is_active=True,
        is_verified=True,
        verification_token=None,
        verification_sent_at=None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    create_audit_log(
        db=db,
        user_id=db_user.id,
        action="register",
        entity_type="user",
        entity_id=db_user.id,
        ip_address=request.client.host if request.client else None
    )
    return db_user

@router.post("/auth/verify-email")
def verify_email(
    *,
    db: Session = Depends(get_db),
    data: VerifyEmailToken,
    request: Request
) -> Any:
    """
    Verify user email with verification token.
    """
    user = db.query(User).filter(User.verification_token == data.token).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token."
        )
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=user.id,
        action="verify_email",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None
    )
    return {"message": "Email verified successfully."}

@router.post("/auth/resend-verification")
def resend_verification(
    *,
    db: Session = Depends(get_db),
    data: ResendVerification,
    request: Request
) -> Any:
    """
    Resend email verification token.
    """
    normalized_email = data.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )
    if user.is_verified:
        return {"message": "Account is already verified."}

    # Cooldown of 60 seconds
    if user.verification_sent_at:
        now = datetime.now(timezone.utc)
        sent_at = user.verification_sent_at
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        if now - sent_at < timedelta(seconds=60):
            raise HTTPException(
                status_code=429,
                detail="Please wait at least 60 seconds before requesting another verification email."
            )

    user.verification_token = str(uuid.uuid4())
    user.verification_sent_at = datetime.now(timezone.utc)
    db.commit()

    create_audit_log(
        db=db,
        user_id=user.id,
        action="resend_verification",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None
    )
    return {"message": "Verification email link sent successfully.", "token": user.verification_token}

@router.post("/auth/change-password")
def change_password(
    *,
    db: Session = Depends(get_db),
    data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Change user password.
    """
    if not security.verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect."
        )
    
    current_user.password_hash = security.get_password_hash(data.new_password)
    db.commit()
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="change_password",
        entity_type="user",
        entity_id=current_user.id,
        ip_address=request.client.host if request.client else None
    )
    return {"message": "Password changed successfully."}

@router.post("/auth/login", response_model=Token)
def login(
    *,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    normalized_email = form_data.username.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, role=user.role.value, expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(user.id, role=user.role.value)
    
    create_audit_log(
        db=db,
        user_id=user.id,
        action="login",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/auth/refresh", response_model=Token)
def refresh_token(
    *,
    db: Session = Depends(get_db),
    refresh_token: str,
    request: Request
) -> Any:
    """
    Refresh access token.
    """
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    access_token = security.create_access_token(user.id, role=user.role.value)
    new_refresh_token = security.create_refresh_token(user.id, role=user.role.value)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token
    }

@router.post("/auth/logout")
def logout(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request: Request
) -> Any:
    """
    Log out active session.
    """
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="logout",
        entity_type="user",
        entity_id=current_user.id,
        ip_address=request.client.host if request.client else None
    )
    return {"detail": "Successfully logged out."}
