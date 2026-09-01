from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, TypeAdapter, ValidationError, field_validator, model_validator


def validate_email(email: str) -> str:
    """Validate and normalize an email for consistent lookup/storage."""
    try:
        validated_email = TypeAdapter(EmailStr).validate_python(email)
    except (ValidationError, TypeError):
        raise ValueError("Please enter a valid email address.") from None
    return str(validated_email).strip().lower()


def validate_password(password: str) -> str:
    """Enforce the registration password policy with a specific error message."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not any(not character.isalnum() and not character.isspace() for character in password):
        raise ValueError("Password must contain at least one special character.")
    return password


class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: Literal["Institution Admin", "Researcher", "Reviewer", "Publisher", "Faculty", "Student", "Collaborator"] = "Researcher"
    institution: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=150)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, full_name: str) -> str:
        normalized_name = " ".join(full_name.split())
        if len(normalized_name) < 2:
            raise ValueError("Please enter a valid full name.")
        return normalized_name

    @field_validator("email")
    @classmethod
    def normalize_email(cls, email: str) -> str:
        return validate_email(email)

    @field_validator("password")
    @classmethod
    def enforce_password_policy(cls, password: str) -> str:
        return validate_password(password)


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, email: str) -> str:
        return validate_email(email)

    @field_validator("password")
    @classmethod
    def require_password(cls, password: str) -> str:
        if not password:
            raise ValueError("Password is required.")
        return password


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    institution_id: int | None = None
    institution: str | None = None
    department: str | None = None
    bio: str | None = None
    research_interests: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    profile_picture: str | None = None
    is_active: bool
    approval_status: str = "Approved"
    email_verified: bool = True
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    institution: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=150)
    bio: str | None = Field(default=None, max_length=2000)
    research_interests: list[str] | None = None
    skills: list[str] | None = None
    profile_picture: str | None = Field(default=None, max_length=500)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def enforce_password_policy(cls, password: str) -> str:
        return validate_password(password)


class CurrentPasswordVerification(BaseModel):
    current_password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class EmailVerificationRequest(BaseModel):
    email: str
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, email: str) -> str:
        return validate_email(email)


class VerificationResendRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, email: str) -> str:
        return validate_email(email)


class PasswordResetRequest(BaseModel):
    email: str | None = None
    identifier: str | None = Field(default=None, min_length=2, max_length=254)

    @model_validator(mode="after")
    def require_identifier(self):
        if not self.email and not self.identifier:
            raise ValueError("Enter your registered email address or username.")
        if self.email:
            self.email = validate_email(self.email)
        if self.identifier:
            self.identifier = self.identifier.strip()
        return self


class PasswordResetConfirm(BaseModel):
    email: str | None = None
    identifier: str | None = Field(default=None, min_length=2, max_length=254)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str

    @model_validator(mode="after")
    def require_identifier(self):
        if not self.email and not self.identifier:
            raise ValueError("Enter your registered email address or username.")
        if self.email:
            self.email = validate_email(self.email)
        if self.identifier:
            self.identifier = self.identifier.strip()
        return self

    @field_validator("new_password")
    @classmethod
    def enforce_password_policy(cls, password: str) -> str:
        return validate_password(password)
