import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SupportMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    # Only used (and required) when a System Admin is sending the message —
    # it tells the API which user's thread the reply belongs to. Ignored
    # for a Researcher/Reviewer/Institution Admin, whose own thread is
    # always their own account.
    thread_user_id: uuid.UUID | None = None


class SupportMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    thread_user_id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str
    sender_role: str
    body: str
    is_from_admin: bool
    is_read: bool
    created_at: datetime


class SupportThreadOut(BaseModel):
    user_id: uuid.UUID
    user_name: str
    user_email: str
    user_role: str
    institution_name: str | None = None
    last_message: str
    last_message_at: datetime
    unread_count: int
