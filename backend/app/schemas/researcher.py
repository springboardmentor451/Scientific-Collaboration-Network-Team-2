from pydantic import BaseModel
from typing import Optional


class ResearcherCreate(BaseModel):
    institution_id: Optional[int] = None
    research_area: Optional[str] = None
    biography: Optional[str] = None
    profile_url: Optional[str] = None


class ResearcherResponse(BaseModel):
    id: int
    user_id: int
    institution_id: Optional[int] = None
    research_area: Optional[str] = None
    biography: Optional[str] = None
    profile_url: Optional[str] = None

    class Config:
        from_attributes = True