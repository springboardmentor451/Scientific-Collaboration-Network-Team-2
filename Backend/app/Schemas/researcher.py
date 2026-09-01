from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.Schemas.user import validate_email


class ResearcherBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str
    department: str = Field(min_length=2, max_length=150)
    institution: str = Field(min_length=2, max_length=200)
    field: str = Field(min_length=2, max_length=200)
    skills: list[str] = Field(default_factory=list)
    research_interests: list[str] = Field(default_factory=list)
    affiliation: str | None = Field(default=None, max_length=200)

    @field_validator("name", "department", "institution", "field")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("affiliation")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        normalized = " ".join(value.split()) if value else None
        return normalized or None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return validate_email(value) if value else None

    @field_validator("skills", "research_interests")
    @classmethod
    def normalize_string_list(cls, values: list[str]) -> list[str]:
        normalized = []
        for value in values:
            item = " ".join(value.split())
            if item and item.casefold() not in {existing.casefold() for existing in normalized}:
                normalized.append(item)
        return normalized


class ResearcherCreate(ResearcherBase):
    pass


class ResearcherUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: str | None = None
    department: str | None = Field(default=None, min_length=2, max_length=150)
    institution: str | None = Field(default=None, min_length=2, max_length=200)
    field: str | None = Field(default=None, min_length=2, max_length=200)
    skills: list[str] | None = None
    research_interests: list[str] | None = None
    affiliation: str | None = Field(default=None, max_length=200)

    @field_validator("name", "department", "institution", "field")
    @classmethod
    def normalize_required_text(cls, value: str | None) -> str | None:
        return " ".join(value.split()) if value else value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return validate_email(value) if value is not None else None

    @field_validator("skills", "research_interests")
    @classmethod
    def normalize_string_list(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        normalized = []
        for value in values:
            item = " ".join(value.split())
            if item and item.casefold() not in {existing.casefold() for existing in normalized}:
                normalized.append(item)
        return normalized


class ResearcherResponse(ResearcherBase):
    id: int
    email: str | None = None
    user_id: int | None = None
    institution_id: int | None = None
    publication_count: int = 0
    collaboration_count: int = 0
    source: str | None = None
    source_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
