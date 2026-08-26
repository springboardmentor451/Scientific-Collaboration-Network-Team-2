import re
import uuid

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.schemas.common import ResearcherOut

ORCID_PATTERN = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    institution_id: uuid.UUID | None = None
    department: str | None = None
    academic_title: str | None = None
    orcid_id: str | None = None

    @field_validator("email")
    @classmethod
    def real_deliverable_email(cls, v: str) -> str:
        """
        Checks not just that the email is correctly *formatted*, but that its
        domain actually has mail servers configured (a DNS MX-record lookup) —
        so obviously fake domains are rejected at registration time, not later.
        """
        try:
            result = validate_email(v, check_deliverability=True)
        except EmailNotValidError as e:
            raise ValueError(str(e))
        return result.normalized

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("full_name cannot be blank")
        return v.strip()

    @field_validator("orcid_id")
    @classmethod
    def orcid_format(cls, v: str | None) -> str | None:
        if v is not None and not ORCID_PATTERN.match(v):
            raise ValueError("orcid_id must be in the format 0000-0000-0000-0000")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OtpRequired(BaseModel):
    """Returned by /auth/login-json instead of a Token — the password was
    correct, but a 6-digit code was just emailed and must be verified via
    /auth/verify-login-otp before an access token is issued."""
    otp_required: bool = True
    email: EmailStr
    message: str = "A 6-digit verification code has been sent to your email."


class VerifyOtp(BaseModel):
    email: EmailStr
    code: str

    @field_validator("code")
    @classmethod
    def code_is_six_digits(cls, v: str) -> str:
        v = v.strip()
        if not re.fullmatch(r"\d{6}", v):
            raise ValueError("code must be exactly 6 digits")
        return v


class ResendOtp(BaseModel):
    email: EmailStr


class GoogleAuth(BaseModel):
    """id_token is the credential Google's Identity Services library hands
    back to the frontend after the user picks a Google account."""
    id_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if len(v) < 8 or not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must be at least 8 characters and include a letter and a number")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if len(v) < 8 or not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must be at least 8 characters and include a letter and a number")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    email_notifications_enabled: bool = True
    researcher: ResearcherOut | None = None


class NotificationPreferenceUpdate(BaseModel):
    email_notifications_enabled: bool
