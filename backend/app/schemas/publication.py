from typing import Optional

from pydantic import BaseModel

from app.models.publication import PublicationStatus, PublicationType
from app.schemas.researcher import ResearcherOut


class PublicationBase(BaseModel):
    title: str
    abstract: Optional[str] = None
    doi: Optional[str] = None
    publication_type: PublicationType = PublicationType.OTHER
    status: PublicationStatus = PublicationStatus.DRAFT
    year: Optional[int] = None
    venue: Optional[str] = None
    file_path: Optional[str] = None


class PublicationCreate(PublicationBase):
    author_ids: list[int] = []


class PublicationUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    doi: Optional[str] = None
    publication_type: Optional[PublicationType] = None
    status: Optional[PublicationStatus] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    file_path: Optional[str] = None
    author_ids: Optional[list[int]] = None


class PublicationOut(PublicationBase):
    id: int
    authors: list[ResearcherOut] = []

    class Config:
        from_attributes = True
