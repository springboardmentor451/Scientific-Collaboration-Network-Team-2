from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class CollaborationRequestCreate(BaseModel):
    researcher_id: int
    message: str | None = Field(default=None, max_length=2000)

class CollaborationRequestResponse(BaseModel):
    id: int
    requester_id: int
    recipient_id: int
    requester_name: str
    recipient_name: str
    message: str | None
    status: Literal["Pending", "Accepted", "Rejected", "Cancelled"]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
