from app.models import UserRole
from pydantic import BaseModel


class UserAdminUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None