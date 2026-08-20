from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ConferenceBase(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    website: Optional[str] = None
    description: Optional[str] = None

class ConferenceCreate(ConferenceBase):
    name: str

class ConferenceUpdate(ConferenceBase):
    pass

class ConferenceInDBBase(ConferenceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConferenceOut(ConferenceInDBBase):
    pass
