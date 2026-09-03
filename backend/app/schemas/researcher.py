from pydantic import BaseModel, EmailStr
from typing import Optional


class ResearcherCreate(BaseModel):
    institution_id: Optional[int] = None
    research_area: Optional[str] = None
    biography: Optional[str] = None
    profile_url: Optional[str] = None


class ResearcherUpdate(BaseModel):
    institution_id: Optional[int] = None
    research_area: Optional[str] = None
    biography: Optional[str] = None
    profile_url: Optional[str] = None


class ResearcherResponse(BaseModel):

    id: int
    user_id: int

    full_name: Optional[str] = None
    email: Optional[str] = None

    institution_id: Optional[int] = None
    institution_name: Optional[str] = None
    country: Optional[str] = None

    research_area: Optional[str] = None
    biography: Optional[str] = None
    profile_url: Optional[str] = None

    h_index: int = 0
    papers: int = 0
    citations: int = 0
    collaborators: int = 0

    status: str = "Active"

    class Config:
        from_attributes = True


class ResearcherAdminCreate(BaseModel):

    full_name: str
    email: EmailStr
    password: str

    institution_id: Optional[int] = None

    research_area: Optional[str] = None
    biography: Optional[str] = None
    profile_url: Optional[str] = None

    status: str = "Active"