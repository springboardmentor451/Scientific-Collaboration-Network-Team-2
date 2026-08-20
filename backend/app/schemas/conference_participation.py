from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.conference_participation import ParticipationRole

class ConferenceParticipationBase(BaseModel):
    conference_id: Optional[int] = None
    researcher_id: Optional[int] = None
    participation_role: Optional[ParticipationRole] = ParticipationRole.attendee
    presentation_title: Optional[str] = None
    registration_date: Optional[date] = None

class ConferenceParticipationCreate(ConferenceParticipationBase):
    conference_id: int
    researcher_id: int

class ConferenceParticipationUpdate(BaseModel):
    participation_role: Optional[ParticipationRole] = None
    presentation_title: Optional[str] = None
    registration_date: Optional[date] = None

class ConferenceParticipationInDBBase(ConferenceParticipationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ConferenceParticipationOut(ConferenceParticipationInDBBase):
    pass
