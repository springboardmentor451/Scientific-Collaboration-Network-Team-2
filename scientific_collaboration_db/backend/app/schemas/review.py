import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReviewerOut(BaseModel):
    """A user with the reviewer role, for admin/institution-admin dropdowns."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    full_name: str | None = None
    institution_id: uuid.UUID | None = None
    institution_name: str | None = None
    is_active: bool = True


class ReviewAssignCreate(BaseModel):
    publication_id: uuid.UUID
    reviewer_id: uuid.UUID
    note: str | None = None


class ReviewDecisionUpdate(BaseModel):
    status: Literal["approved", "changes_requested", "rejected"]
    comments: str | None = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    publication_id: uuid.UUID
    publication_title: str | None = None
    publication_status: str | None = None
    reviewer_id: uuid.UUID
    reviewer_name: str | None = None
    reviewer_email: str | None = None
    assigned_by_id: uuid.UUID | None = None
    assigned_by_email: str | None = None
    status: str
    note: str | None = None
    comments: str | None = None
    assigned_at: datetime
    decided_at: datetime | None = None
