import re
import uuid
from datetime import date

from pydantic import BaseModel, field_validator, model_validator

from app.models.publication import PublicationStatus, PublicationType

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")

# Which status transitions are allowed on update (simple forward-moving workflow,
# plus admins can always move something to "archived").
ALLOWED_STATUS_TRANSITIONS = {
    PublicationStatus.DRAFT: {PublicationStatus.SUBMITTED, PublicationStatus.ARCHIVED},
    PublicationStatus.SUBMITTED: {PublicationStatus.PUBLISHED, PublicationStatus.DRAFT, PublicationStatus.ARCHIVED},
    PublicationStatus.PUBLISHED: {PublicationStatus.ARCHIVED},
    PublicationStatus.ARCHIVED: set(),
}


class PublicationCreate(BaseModel):
    title: str
    abstract: str | None = None
    publication_type: PublicationType
    doi: str | None = None
    journal_or_venue: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    publication_date: date | None = None
    project_id: uuid.UUID | None = None
    co_author_ids: list[uuid.UUID] = []  # additional authors beyond the submitter

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title cannot be blank")
        if len(v) > 500:
            raise ValueError("title must be 500 characters or fewer")
        return v.strip()

    @field_validator("doi")
    @classmethod
    def doi_format(cls, v: str | None) -> str | None:
        if v is not None and not DOI_PATTERN.match(v):
            raise ValueError("doi must look like 10.xxxx/suffix")
        return v


class PublicationUpdate(BaseModel):
    title: str | None = None
    abstract: str | None = None
    status: PublicationStatus | None = None
    doi: str | None = None
    journal_or_venue: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    publication_date: date | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title cannot be blank")
        return v.strip() if v else v

    @field_validator("doi")
    @classmethod
    def doi_format(cls, v: str | None) -> str | None:
        if v is not None and not DOI_PATTERN.match(v):
            raise ValueError("doi must look like 10.xxxx/suffix")
        return v
