from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.notifications import NotificationChannel, NotificationStatus

class NotificationBase(BaseModel):
    user_id: Optional[int] = None
    channel: Optional[NotificationChannel] = NotificationChannel.in_app
    subject: Optional[str] = None
    body: Optional[str] = None
    status: Optional[NotificationStatus] = NotificationStatus.sent
    is_read: Optional[bool] = False

class NotificationCreate(NotificationBase):
    user_id: int
    body: str

class NotificationOut(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
