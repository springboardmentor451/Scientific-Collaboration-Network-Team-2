from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.RESEARCHER
    researcher_id: Optional[int] = None
    institution_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    researcher_id: Optional[int] = None
    institution_id: Optional[int] = None


class UserOut(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
