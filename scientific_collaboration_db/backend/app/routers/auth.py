"""
Authentication endpoints: register, login, and "who am I".
"""
# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.orm import Session

# from app.core.deps import get_current_user
# from app.core.config import get_settings
# from app.core.email import send_verification_email
# from app.core.security import create_access_token, create_email_verification_token, decode_access_token, hash_password, verify_password
# from app.database import get_db
# from app.models import Researcher, User, UserRole
# from app.schemas.auth import Token, UserLogin, UserOut, UserRegister

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.config import get_settings
from app.core.email import send_otp_email, send_verification_email
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    decode_access_token,
    generate_otp_code,
    hash_otp_code,
    hash_password,
    verify_otp_code,
    verify_password,
)
from app.database import get_db
from app.models import LoginOtp, Researcher, User, UserRole
from app.schemas.auth import GoogleAuth, OtpRequired, ResendOtp, Token, UserLogin, UserOut, UserRegister, VerifyOtp


# _____________


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

    # Dev convenience: when no real SMTP account is configured, there is no
    # way for the frontend to actually receive the verification email, so we
    # skip the verification gate entirely and mark the account verified
    # immediately. In production, configure SMTP_* and this becomes False,
    # restoring the real "click the emailed link" flow.
    smtp_configured = bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD and settings.SMTP_FROM_EMAIL)

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.RESEARCHER,
        is_verified=not smtp_configured,
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


# @router.post("/login-json", response_model=Token)
# def login_json(payload: UserLogin, db: Session = Depends(get_db)):
#     """Plain JSON login alternative, for non-Swagger clients (e.g. a future frontend)."""
#     user = db.query(User).filter(User.email == payload.email).first()
#     if not user or not verify_password(payload.password, user.hashed_password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
#     if not user.is_active:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
#     if not user.is_verified:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Please verify your email before logging in. Check your inbox for the verification link.",
#         )

#     token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
#     return Token(access_token=token)

def _issue_login_otp(db: Session, user: User) -> None:
    """Invalidate any earlier unused codes, generate + store + email a fresh one."""
    db.query(LoginOtp).filter(LoginOtp.user_id == user.id, LoginOtp.used == False).update({"used": True})  # noqa: E712
    code = generate_otp_code()
    otp = LoginOtp(
        user_id=user.id,
        code_hash=hash_otp_code(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.LOGIN_OTP_EXPIRE_MINUTES),
    )
    db.add(otp)
    db.commit()
    send_otp_email(user.email, code)


@router.post("/login-json", response_model=OtpRequired)
def login_json(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Step 1 of 2. Verifies the password, then emails a real 6-digit code and
    returns {otp_required: true} instead of a token. Call
    /auth/verify-login-otp with that code to actually get an access token.

    (If SMTP isn't configured in .env, the code is logged to the backend's
    console/log instead of emailed — see app/core/email.py.)
    """
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

    _issue_login_otp(db, user)
    return OtpRequired(email=user.email)


@router.post("/resend-login-otp")
def resend_login_otp(payload: ResendOtp, db: Session = Depends(get_db)):
    """Sends a fresh code, invalidating any earlier unused one for this account."""
    user = db.query(User).filter(User.email == payload.email).first()
    if user and user.is_active and user.is_verified:
        _issue_login_otp(db, user)
    return {"message": "If that account exists, a new code has been sent."}


@router.post("/verify-login-otp", response_model=Token)
def verify_login_otp(payload: VerifyOtp, db: Session = Depends(get_db)):
    """Step 2 of 2. Exchanges a valid, unexpired, unused code for a real access token."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or code")

    otp = (
        db.query(LoginOtp)
        .filter(LoginOtp.user_id == user.id, LoginOtp.used == False)  # noqa: E712
        .order_by(LoginOtp.created_at.desc())
        .first()
    )
    if not otp or otp.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code has expired. Request a new one.")
    if not verify_otp_code(payload.code, otp.code_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect code.")

    otp.used = True
    db.commit()

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    return Token(access_token=token)


@router.post("/google", response_model=Token)
def google_login(payload: GoogleAuth, db: Session = Depends(get_db)):
    """
    'Continue with Google'. Verifies the ID token Google's Identity Services
    JS library hands to the frontend, then logs in (or silently creates) the
    matching account. No OTP step here — Google has already authenticated
    the person.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google sign-in is not configured on this server. Set GOOGLE_CLIENT_ID in backend/.env.",
        )

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token

        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential.")

    if not idinfo.get("email_verified", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google account email is not verified.")

    email = idinfo["email"]
    full_name = idinfo.get("name") or email.split("@")[0]

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        import secrets as _secrets

        user = User(
            email=email,
            hashed_password=hash_password(_secrets.token_urlsafe(32)),
            role=UserRole.RESEARCHER,
            is_verified=True,
        )
        db.add(user)
        db.flush()
        db.add(Researcher(user_id=user.id, full_name=full_name))
        db.commit()
        db.refresh(user)
    elif not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    return Token(access_token=token)

# ____________



@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
