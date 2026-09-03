from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PublicationCreate(BaseModel):

    title: str
    abstract: Optional[str] = None
    publication_type: Optional[str] = None
    journal_name: Optional[str] = None
    doi: Optional[str] = None
    publication_date: Optional[date] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    url: Optional[str] = None
    citation_count: int = 0


class PublicationResponse(BaseModel):

    id: int
    title: str
    abstract: Optional[str] = None
    publication_type: Optional[str] = None
    journal_name: Optional[str] = None
    doi: Optional[str] = None
    publication_date: Optional[date] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    url: Optional[str] = None
    pdf_file: Optional[str] = None
    citation_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )