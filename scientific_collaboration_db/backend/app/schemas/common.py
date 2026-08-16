# import uuid
# from datetime import date, datetime

# from pydantic import BaseModel, ConfigDict


# class InstitutionOut(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     id: uuid.UUID
#     name: str
#     country: str | None
#     institution_type: str | None


# class ResearcherOut(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     id: uuid.UUID
#     full_name: str
#     department: str | None
#     academic_title: str | None
#     orcid_id: str | None
#     institution: InstitutionOut | None = None


# class PublicationOut(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     id: uuid.UUID
#     title: str
#     publication_type: str
#     status: str
#     doi: str | None
#     journal_or_venue: str | None
#     publication_date: date | None


# class ProjectOut(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     id: uuid.UUID
#     title: str
#     status: str
#     start_date: date | None
#     end_date: date | None
#     funding_source: str | None


# class ConferenceOut(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     id: uuid.UUID
#     name: str
#     location: str | None
#     start_date: date | None
#     end_date: date | None

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
    author_names: list[str] = []


class ProjectMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    researcher_id: uuid.UUID
    role: str
    full_name: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    status: str
    start_date: date | None
    end_date: date | None
    funding_source: str | None
    lead_institution: InstitutionOut | None = None
    lead_researcher_name: str | None = None
    member_names: list[str] = []


class ConferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    location: str | None
    start_date: date | None
    end_date: date | None


class CitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    citing_publication_id: uuid.UUID
    cited_publication_id: uuid.UUID | None
    external_title: str | None
    external_doi: str | None
    external_authors: str | None
    created_at: datetime


class ParticipationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    conference_id: uuid.UUID
    researcher_id: uuid.UUID
    publication_id: uuid.UUID | None
    role: str
    presentation_title: str | None
    registered_at: datetime