import hashlib
import hmac
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.Crud.user import create_user, get_user_by_email
from app.Schemas.user import CurrentPasswordVerification, EmailVerificationRequest, PasswordChange, PasswordResetConfirm, PasswordResetRequest, TokenResponse, UserCreate, UserLogin, UserResponse, UserUpdate, VerificationResendRequest
from app.Utils.auth import hash_password, verify_password
from app.core.security import create_access_token, get_current_user
from app.models.user import User
from app.models.institution import Institution
from app.models.researcher import Researcher
from app.models.publication import Publication
from app.models.project import Project
from app.models.collaboration import CollaborationRequest
from app.models.conference import conference_participants
from sqlalchemy import func
from app.Crud.audit import log_action
from app.core.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/users", tags=["Users"])

VERIFICATION_TTL_MINUTES = 10
VERIFICATION_RESEND_COOLDOWN_SECONDS = 60
VERIFICATION_MAX_ATTEMPTS = 5


def _code_hash(email: str, code: str) -> str:
    secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY") or "change-this-development-secret-before-production"
    return hmac.new(secret.encode(), f"{email}:{code}".encode(), hashlib.sha256).hexdigest()


def _issue_verification_code(user: User, db: Session) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.now(timezone.utc)
    user.verification_code_hash = _code_hash(user.email, code)
    user.verification_code_expires_at = now + timedelta(minutes=VERIFICATION_TTL_MINUTES)
    user.verification_code_sent_at = now
    user.verification_attempts = 0
    db.commit()
    return code


def _issue_reset_code(user: User, db: Session) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"; now = datetime.now(timezone.utc)
    user.password_reset_code_hash = _code_hash(user.email, code); user.password_reset_code_expires_at = now + timedelta(minutes=VERIFICATION_TTL_MINUTES)
    user.password_reset_code_sent_at = now; user.password_reset_attempts = 0; db.commit(); return code


def _get_user_for_password_reset(db: Session, email: str | None, identifier: str | None) -> User | None:
    """Accept an email or the account's displayed username (full name) without revealing account existence."""
    lookup = (email or identifier or "").strip()
    if not lookup:
        return None
    if "@" in lookup:
        return get_user_by_email(db, lookup)
    normalized_name = " ".join(lookup.split()).lower()
    return db.query(User).filter(func.lower(User.full_name) == normalized_name).first()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user.email)

    if existing_user:
        if not existing_user.email_verified:
            raise HTTPException(status_code=409, detail="An unverified account already exists for this email. Open Verify Email and request a new code.")
        raise HTTPException(status_code=400, detail="Email already registered.")

    new_user = create_user(db, user)
    new_user.email_verified = False
    code = _issue_verification_code(new_user, db)
    try:
        send_verification_email(new_user.email, new_user.full_name, code)
    except (RuntimeError, OSError, smtplib.SMTPException) as error:
        # Do not reserve an email address when delivery failed. This lets the
        # user correct their address and register again without Admin help.
        db.delete(new_user)
        db.commit()
        raise HTTPException(status_code=503, detail=f"Verification email could not be sent. Please try again. {error}") from None
    log_action(db, "USER_REGISTERED", new_user.id, "User", new_user.id, f"Role: {new_user.role}")
    log_action(db, "EMAIL_VERIFICATION_SENT", new_user.id, "User", new_user.id)
    db.commit()

    return new_user


@router.post("/verify-email")
def verify_email(data: EmailVerificationRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification request.")
    if user.email_verified:
        return {"message": "Email is already verified."}
    now = datetime.now(timezone.utc)
    expires_at = user.verification_code_expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not user.verification_code_hash or not expires_at or expires_at < now:
        raise HTTPException(status_code=400, detail="This verification code has expired. Request a new code.")
    if user.verification_attempts >= VERIFICATION_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many incorrect attempts. Request a new verification code.")
    user.verification_attempts += 1
    if not hmac.compare_digest(user.verification_code_hash, _code_hash(user.email, data.code)):
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect verification code.")
    user.email_verified = True
    # A verified email is the account-activation check for every public role.
    # Administrative controls remain protected by role-based JWT checks.
    user.approval_status = "Approved"
    user.verification_code_hash = None
    user.verification_code_expires_at = None
    user.verification_attempts = 0
    log_action(db, "EMAIL_VERIFIED", user.id, "User", user.id)
    db.commit()
    return {"message": "Email verified successfully. You can now log in."}


@router.post("/resend-verification")
def resend_verification(data: VerificationResendRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, data.email)
    # Do not disclose whether an email has an account.
    generic_response = {"message": "If an unverified account exists, a verification code has been sent."}
    if not user or user.email_verified:
        return generic_response
    now = datetime.now(timezone.utc)
    if user.verification_code_sent_at and (now - user.verification_code_sent_at).total_seconds() < VERIFICATION_RESEND_COOLDOWN_SECONDS:
        raise HTTPException(status_code=429, detail="Please wait one minute before requesting another code.")
    code = _issue_verification_code(user, db)
    try:
        send_verification_email(user.email, user.full_name, code)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=f"Verification email could not be sent. {error}") from None
    log_action(db, "EMAIL_VERIFICATION_RESENT", user.id, "User", user.id)
    db.commit()
    return generic_response


@router.post("/password-reset/request")
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    user = _get_user_for_password_reset(db, data.email, data.identifier)
    response = {"message": "If an account exists for this email, a password-reset code has been sent."}
    if not user or not user.email_verified: return response
    now = datetime.now(timezone.utc)
    if user.password_reset_code_sent_at and (now - user.password_reset_code_sent_at).total_seconds() < VERIFICATION_RESEND_COOLDOWN_SECONDS:
        raise HTTPException(429, "Please wait one minute before requesting another reset code.")
    code = _issue_reset_code(user, db)
    try: send_password_reset_email(user.email, user.full_name, code)
    except (RuntimeError, OSError, smtplib.SMTPException) as error: raise HTTPException(503, f"Password-reset email could not be sent. {error}") from None
    log_action(db, "PASSWORD_RESET_REQUESTED", user.id, "User", user.id); db.commit(); return response


@router.post("/password-reset/confirm")
def confirm_password_reset(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = _get_user_for_password_reset(db, data.email, data.identifier)
    if not user: raise HTTPException(400, "Invalid password-reset request.")
    expires_at = user.password_reset_code_expires_at
    if expires_at and expires_at.tzinfo is None: expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not user.password_reset_code_hash or not expires_at or expires_at < datetime.now(timezone.utc): raise HTTPException(400, "This reset code has expired. Request a new code.")
    if user.password_reset_attempts >= VERIFICATION_MAX_ATTEMPTS: raise HTTPException(429, "Too many incorrect attempts. Request a new reset code.")
    user.password_reset_attempts += 1
    if not hmac.compare_digest(user.password_reset_code_hash, _code_hash(user.email, data.code)):
        db.commit(); raise HTTPException(400, "Incorrect reset code.")
    user.password = hash_password(data.new_password); user.password_reset_code_hash = None; user.password_reset_code_expires_at = None; user.password_reset_attempts = 0
    log_action(db, "PASSWORD_RESET_COMPLETED", user.id, "User", user.id); db.commit(); return {"message": "Password reset successfully. You can now log in."}


@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not db_user.is_active:
        raise HTTPException(status_code=403, detail="This account is inactive.")
    if not db_user.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email address before logging in.")
    # Email verification is the activation step for public registrations.  This
    # also repairs older verified records that were created before automatic
    # approval replaced the manual approval flow.
    if db_user.approval_status == "Pending":
        db_user.approval_status = "Approved"
        log_action(db, "ACCOUNT_AUTO_APPROVED", db_user.id, "User", db_user.id, "Verified email account activated.")
    if db_user.approval_status == "Rejected":
        raise HTTPException(status_code=403, detail="This account registration was rejected.")
    log_action(db, "USER_LOGIN", db_user.id, "User", db_user.id)
    db.commit()
    return {"access_token": create_access_token(db_user), "token_type": "bearer", "user": db_user}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/workspace")
def get_my_workspace(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Role-safe quick counts used by the persistent application shell."""
    user_id = current_user.id
    collaborations = db.query(CollaborationRequest).filter(
        (CollaborationRequest.requester_id == user_id) | (CollaborationRequest.recipient_id == user_id)
    )
    return {
        "user": UserResponse.model_validate(current_user),
        "publications": db.query(Publication).filter(Publication.owner_id == user_id).count(),
        "projects": db.query(Project).filter(Project.owner_id == user_id).count(),
        "pending_collaborations": collaborations.filter(CollaborationRequest.status == "Pending").count(),
        "accepted_collaborations": collaborations.filter(CollaborationRequest.status == "Accepted").count(),
        "conference_registrations": db.query(conference_participants).filter(conference_participants.c.user_id == user_id).count(),
    }


@router.post("/logout", status_code=200)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Access JWTs are stateless; the client clears its copy.  Logging this makes
    # the action auditable without pretending that a token was server-revoked.
    log_action(db, "USER_LOGOUT", current_user.id, "User", current_user.id)
    db.commit()
    return {"message": f"{current_user.full_name} logged out successfully."}


@router.put("/me", response_model=UserResponse)
def update_me(update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role in {"Admin", "System Admin"}:
        raise HTTPException(status_code=403, detail="System Admin account details are managed by the platform and cannot be edited here.")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    if "institution" in update.model_fields_set:
        institution = db.query(Institution).filter(func.lower(Institution.name) == current_user.institution.lower()).first() if current_user.institution else None
        current_user.institution_id = institution.id if institution else None
    profile = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    if profile:
        profile.name = current_user.full_name
        profile.department = current_user.department or profile.department
        profile.institution = current_user.institution or profile.institution
        profile.institution_id = current_user.institution_id
        profile.skills = current_user.skills or []
        profile.research_interests = current_user.research_interests or []
    db.commit()
    log_action(db, "PROFILE_UPDATED", current_user.id, "User", current_user.id)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/password")
def change_my_password(data: PasswordChange, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Change a password only after the currently authenticated user proves their existing password."""
    if not verify_password(data.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Your current password is incorrect.")
    if verify_password(data.new_password, current_user.password):
        raise HTTPException(status_code=400, detail="Choose a new password that is different from your current password.")
    current_user.password = hash_password(data.new_password)
    log_action(db, "PASSWORD_CHANGED", current_user.id, "Security", current_user.id, "Password changed from authenticated account settings.")
    db.commit()
    return {"message": "Password changed successfully."}


@router.post("/me/password/verify")
def verify_current_password(data: CurrentPasswordVerification, current_user: User = Depends(get_current_user)):
    if not verify_password(data.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Your current password is incorrect.")
    return {"message": "Current password verified."}
