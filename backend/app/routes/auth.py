import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.auth.hash import hash_password, verify_password
from backend.app.auth.jwt_handler import create_access_token
from backend.app.auth.oauth2 import get_current_user
from backend.app.database.session import get_db
from backend.app.models.users import User
from backend.app.models.captcha_challenges import CaptchaChallenge
from backend.app.schemas.user import (
    CaptchaStartRequest,
    CaptchaVerifyRequest,
    CaptchaResponse,
    UserRegister,
    UserLogin,
    UserResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

def _hash_captcha_answer(answer: str):
    return hashlib.sha256(answer.strip().lower().encode("utf-8")).hexdigest()


def _generate_captcha():
    captcha = f"{secrets.randbelow(1000000):06d}"
    return captcha, captcha


def _clean_expired_captchas(db: Session):
    db.query(CaptchaChallenge).filter(
        CaptchaChallenge.expires_at < datetime.now(timezone.utc)
    ).delete(synchronize_session=False)
    db.commit()


@router.get("/captcha", response_model=CaptchaResponse)
def get_captcha(
    db: Session = Depends(get_db)
):
    _clean_expired_captchas(db)
    question, answer = _generate_captcha()
    challenge = CaptchaChallenge(
        challenge_id=secrets.token_urlsafe(32),
        answer_hash=_hash_captcha_answer(answer),
        expires_at=None,
        used=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(challenge)
    db.commit()
    return CaptchaResponse(
        challenge_id=challenge.challenge_id,
        question=question,
        expires_in=15,
    )


@router.post("/captcha/start")
def start_captcha(
    request: CaptchaStartRequest,
    db: Session = Depends(get_db),
):
    captcha = db.query(CaptchaChallenge).filter(
        CaptchaChallenge.challenge_id == request.challenge_id,
        CaptchaChallenge.used.is_(False),
    ).first()

    if not captcha:
        raise HTTPException(status_code=400, detail="CAPTCHA not found. Please generate a new one.")

    if captcha.expires_at is None:
        captcha.expires_at = datetime.now(timezone.utc) + timedelta(seconds=15)
        db.commit()

    return {"expires_in": 15}


@router.post("/captcha/verify")
def verify_captcha(
    request: CaptchaVerifyRequest,
    db: Session = Depends(get_db),
):
    _clean_expired_captchas(db)
    captcha = db.query(CaptchaChallenge).filter(
        CaptchaChallenge.challenge_id == request.challenge_id,
        CaptchaChallenge.used.is_(False),
    ).first()

    if not captcha:
        raise HTTPException(
            status_code=400,
            detail="CAPTCHA not found or expired. Please generate a new one.",
        )

    if captcha.expires_at is None:
        raise HTTPException(status_code=400, detail="CAPTCHA has not started. Click the answer field first.")

    if not hmac.compare_digest(
        captcha.answer_hash,
        _hash_captcha_answer(request.answer),
    ):
        raise HTTPException(status_code=400, detail="Incorrect CAPTCHA answer.")

    captcha.verified = True
    captcha.expires_at = None
    db.commit()
    return {"message": "CAPTCHA verified successfully."}


@router.post("/register", response_model=UserResponse)
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    email_key = user.email.lower().strip()

    existing_user = (
        db.query(User)
        .filter(User.email == email_key)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    _clean_expired_captchas(db)
    captcha = db.query(CaptchaChallenge).filter(
        CaptchaChallenge.challenge_id == user.captcha_id,
        CaptchaChallenge.used.is_(False),
        CaptchaChallenge.verified.is_(True),
    ).first()

    if not captcha:
        raise HTTPException(
            status_code=400,
            detail="CAPTCHA must be verified before registration. Please verify a new CAPTCHA."
        )

    if captcha.expires_at is not None and captcha.expires_at < datetime.now(timezone.utc):
        db.delete(captcha)
        db.commit()
        raise HTTPException(status_code=400, detail="CAPTCHA expired. Please generate a new one.")

    if not hmac.compare_digest(
        captcha.answer_hash,
        _hash_captcha_answer(user.captcha_answer),
    ):
        raise HTTPException(status_code=400, detail="Incorrect CAPTCHA answer.")

    hashed_password = hash_password(user.password)

    new_user = User(
        full_name=user.full_name,
        email=email_key,
        password_hash=hashed_password,
        role=user.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    db.delete(captcha)
    db.commit()

    return new_user

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        form_data.password,
        existing_user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={
            "sub": str(existing_user.id),
            "email": existing_user.email,
            "role": existing_user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = db.query(User).filter(
        User.id == int(current_user.get("sub"))
    ).first()

    return {
        "user_id": current_user.get("sub"),
        "id": user.id if user else int(current_user.get("sub")),
        "full_name": user.full_name if user else current_user.get("email"),
        "email": user.email if user else current_user.get("email"),
        "role": user.role if user else current_user.get("role"),
        "avatar_url": user.avatar_url if user else None,
        "is_active": user.is_active if user else True
    }