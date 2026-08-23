from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.models.conference import ParticipationRole


class ConferenceBase(BaseModel):
    name: str
    location: Optional[str] = None
    website: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ConferenceCreate(ConferenceBase):
    pass


class ConferenceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ConferenceOut(ConferenceBase):
    id: int

    class Config:
        from_attributes = True


class ParticipationBase(BaseModel):
    conference_id: int
    researcher_id: int
    publication_id: Optional[int] = None
    role: ParticipationRole = ParticipationRole.ATTENDEE
    presentation_title: Optional[str] = None


class ParticipationCreate(ParticipationBase):
    pass


class ParticipationUpdate(BaseModel):
    role: Optional[ParticipationRole] = None
    presentation_title: Optional[str] = None
    publication_id: Optional[int] = None


class ParticipationOut(ParticipationBase):
    id: int

    class Config:
        from_attributes = True
