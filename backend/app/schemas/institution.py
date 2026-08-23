from pydantic import BaseModel
from typing import Optional


class InstitutionBase(BaseModel):
    name: str
    type: Optional[str] = None
    country: Optional[str] = None


class InstitutionCreate(InstitutionBase):
    pass


class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    country: Optional[str] = None


class InstitutionOut(InstitutionBase):
    id: int

    class Config:
        from_attributes = True