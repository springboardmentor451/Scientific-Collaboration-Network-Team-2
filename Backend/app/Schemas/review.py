from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class ReviewAssign(BaseModel):
    publication_id: int
    reviewer_id: int

class ReviewDecision(BaseModel):
    status: Literal["Approved", "Rejected"]
    comments: str | None = Field(default=None, max_length=5000)

class ReviewResponse(BaseModel):
    id: int
    publication_id: int
    reviewer_id: int
    assigned_by_id: int | None
    status: str
    comments: str | None
    created_at: datetime
    decided_at: datetime | None
    publication_title: str | None = None
    publication_authors: str | None = None
    publication_abstract: str | None = None
    publication_document_path: str | None = None
    model_config = ConfigDict(from_attributes=True)
