import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class InstitutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    country: str | None
    institution_type: str | None


class ResearcherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    department: str | None
    academic_title: str | None
    orcid_id: str | None
    institution: InstitutionOut | None = None


class PublicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    publication_type: str
    status: str
    doi: str | None
    journal_or_venue: str | None
    publication_date: date | None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    status: str
    start_date: date | None
    end_date: date | None
    funding_source: str | None


class ConferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    location: str | None
    start_date: date | None
    end_date: date | None
