from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from backend.app.models.publications import PublicationType, PublicationStatus

class PublicationBase(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    type: Optional[PublicationType] = PublicationType.journal_paper
    status: Optional[PublicationStatus] = PublicationStatus.draft
    doi: Optional[str] = None
    venue: Optional[str] = None
    publication_date: Optional[date] = None
    file_url: Optional[str] = None

class PublicationCreate(PublicationBase):
    title: str

class PublicationUpdate(PublicationBase):
    pass

class PublicationInDBBase(PublicationBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

from backend.app.schemas.researchers import ResearcherOut

class PublicationOut(PublicationInDBBase):
    authors: Optional[List[ResearcherOut]] = []
