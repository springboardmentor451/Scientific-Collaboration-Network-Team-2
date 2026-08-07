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


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    researcher: ResearcherOut | None = None
