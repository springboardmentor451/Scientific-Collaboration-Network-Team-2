import re
import uuid

from pydantic import BaseModel, field_validator

ORCID_PATTERN = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")


class ResearcherUpdate(BaseModel):
    """All fields optional — only the ones supplied get updated (partial update)."""
    full_name: str | None = None
    department: str | None = None
    academic_title: str | None = None
    bio: str | None = None
    institution_id: uuid.UUID | None = None
    orcid_id: str | None = None

    @field_validator("full_name")
    @classmethod
    def not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("full_name cannot be blank")
        return v.strip() if v else v

    @field_validator("orcid_id")
    @classmethod
    def orcid_format(cls, v: str | None) -> str | None:
        if v is not None and not ORCID_PATTERN.match(v):
            raise ValueError("orcid_id must be in the format 0000-0000-0000-0000")
        return v


class ResearcherTagsUpdate(BaseModel):
    """Replaces the logged-in researcher's full skill/interest tag set."""
    skills: list[str] = []
    interests: list[str] = []
