"""
Authentication endpoints: register, login, and "who am I".
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.config import get_settings
from app.core.email import send_verification_email
from app.core.security import create_access_token, create_email_verification_token, decode_access_token, hash_password, verify_password
from app.database import get_db
from app.models import Researcher, User, UserRole
from app.schemas.auth import Token, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Creates a User (login account, unverified) plus its linked Researcher
    profile, then sends a real verification email. Validates: email format
    AND deliverability (the domain must actually accept mail) & uniqueness,
    password strength, ORCID format.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    if payload.orcid_id:
        existing_orcid = db.query(Researcher).filter(Researcher.orcid_id == payload.orcid_id).first()
        if existing_orcid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ORCID ID is already in use")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.RESEARCHER,
        is_verified=False,
    )
    db.add(user)
    db.flush()  # get user.id without committing yet

    researcher = Researcher(
        user_id=user.id,
        institution_id=payload.institution_id,
        full_name=payload.full_name,
        department=payload.department,
        academic_title=payload.academic_title,
        orcid_id=payload.orcid_id,
    )
    db.add(researcher)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create account — check that the institution_id exists and details are unique.",
        )

    db.refresh(user)

    verification_token = create_email_verification_token(str(user.id))
    verification_link = f"{settings.API_BASE_URL}/auth/verify-email?token={verification_token}"
    send_verification_email(user.email, verification_link)

    return user


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Called when the user clicks the link sent to their real email address."""
    credentials_error = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification link")
    try:
        payload = decode_access_token(token)
    except Exception:
        raise credentials_error

    if payload.get("purpose") != "email_verification":
        raise credentials_error

    user = db.get(User, payload.get("sub"))
    if not user:
        raise credentials_error

    if user.is_verified:
        return {"message": "Email already verified. You can log in."}

    user.is_verified = True
    db.commit()
    return {"message": "Email verified successfully. You can now log in."}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2-compatible login (username field holds the email). This shape lets
    Swagger's 'Authorize' button work out of the box.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox for the verification link.",
        )

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    return Token(access_token=token)


@router.post("/login-json", response_model=Token)
def login_json(payload: UserLogin, db: Session = Depends(get_db)):
    """Plain JSON login alternative, for non-Swagger clients (e.g. a future frontend)."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox for the verification link.",
        )

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
