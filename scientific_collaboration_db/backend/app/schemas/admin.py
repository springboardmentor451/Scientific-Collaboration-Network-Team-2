import uuid

from app.models import UserRole
from pydantic import BaseModel, EmailStr


class UserAdminUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
    institution_id: uuid.UUID | None = None


class StaffAccountCreate(BaseModel):
    """
    System Admin / Institution Admin onboarding for non-researcher staff
    accounts — Reviewers and (system_admin only) other Institution Admins.
    Mirrors AdminCreateResearcher in routers/admin.py: creates the account
    and emails a real password-reset link, nothing to share manually.
    """
    email: EmailStr
    full_name: str
    role: UserRole
    institution_id: uuid.UUID | None = None