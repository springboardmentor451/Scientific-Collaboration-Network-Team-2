from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime
    method: str
    path: str
    status_code: Optional[int] = None
    user_id: Optional[int] = None
    user_role: Optional[str] = None
    client_ip: Optional[str] = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True
