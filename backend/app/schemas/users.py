import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from email_validator import validate_email, EmailNotValidError
from backend.app.models.users import UserRole

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = UserRole.researcher
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_strict(cls, v: EmailStr) -> EmailStr:
        if not v:
            return v
        email_str = str(v).strip().lower()
        
        # Reject obviously invalid/mock domains
        invalid_domains = ["example.com", "test.com", "invalid.com", "localhost"]
        parts = email_str.split("@")
        if len(parts) < 2:
            raise ValueError("Invalid email format.")
        domain = parts[-1]
        if domain in invalid_domains:
            raise ValueError(f"Domain {domain} is not permitted for registration.")
            
        # Deliverability check with whitelist for test domains
        test_domains = ["scna.org"]
        if domain not in test_domains:
            try:
                validate_email(email_str, check_deliverability=True)
            except EmailNotValidError as e:
                raise ValueError(f"Email deliverability validation failed: {str(e)}")
        return email_str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", v):
            raise ValueError("Password must contain at least one special character.")
        return v

# Properties to receive via API on update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", v):
            raise ValueError("Password must contain at least one special character.")
        return v

class VerifyEmailToken(BaseModel):
    token: str

class ResendVerification(BaseModel):
    email: EmailStr

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    verification_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Additional properties to return via API
class UserOut(UserInDBBase):
    pass

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    role: Optional[str] = None
