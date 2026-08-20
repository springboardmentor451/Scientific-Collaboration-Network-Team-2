import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator
from backend.app.models.researchers import GenderEnum

class ResearcherBase(BaseModel):
    full_name: Optional[str] = None
    institution_id: Optional[int] = None
    department_id: Optional[int] = None
    institution_name: Optional[str] = None
    department_name: Optional[str] = None
    
    # Demographics
    gender: Optional[GenderEnum] = GenderEnum.prefer_not_to_say
    gender_other: Optional[str] = None
    nationality: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    mobile_number: Optional[str] = None
    
    # Academic
    designation: Optional[str] = None
    highest_qualification: Optional[str] = None
    year_highest_qualification: Optional[int] = None

    # External IDs
    orcid_id: Optional[str] = None
    google_scholar_url: Optional[str] = None
    researchgate_url: Optional[str] = None
    scopus_id: Optional[str] = None
    wos_id: Optional[str] = None

    research_interests: Optional[List[str]] = []
    skills: Optional[List[str]] = []
    affiliations: Optional[str] = None
    bio: Optional[str] = None
    profile_photo_url: Optional[str] = None

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        # Must contain EXACTLY 10 digits, numbers only, no spaces, hyphens, brackets, or plus sign
        if not re.match(r"^[0-9]{10}$", v):
            raise ValueError("Mobile number must contain exactly 10 digits.")
        return v

class ResearcherCreate(ResearcherBase):
    user_id: int
    full_name: str
    orcid_id: str

class ResearcherUpdate(ResearcherBase):
    pass

class ResearcherInDBBase(ResearcherBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResearcherOut(ResearcherInDBBase):
    pass
