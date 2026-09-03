from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ConferenceBase(BaseModel):

    name: str = Field(
        ...,
        min_length=1,
        max_length=255
    )

    description: Optional[str] = None

    organizer: Optional[str] = Field(
        default=None,
        max_length=255
    )

    location: Optional[str] = Field(
        default=None,
        max_length=255
    )

    start_date: Optional[date] = None

    end_date: Optional[date] = None

    field: Optional[str] = Field(
        default=None,
        max_length=150
    )

    website: Optional[HttpUrl] = None


class ConferenceCreate(ConferenceBase):
    pass


class ConferenceUpdate(BaseModel):

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255
    )

    description: Optional[str] = None

    organizer: Optional[str] = Field(
        default=None,
        max_length=255
    )

    location: Optional[str] = Field(
        default=None,
        max_length=255
    )

    start_date: Optional[date] = None

    end_date: Optional[date] = None

    field: Optional[str] = Field(
        default=None,
        max_length=150
    )

    website: Optional[HttpUrl] = None


class ConferenceResponse(ConferenceBase):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    status: str

    created_at: datetime

    updated_at: datetime


class ConferenceParticipantCreate(BaseModel):

    researcher_id: int

    role: Optional[str] = Field(
        default=None,
        max_length=100
    )

    registration_status: str = Field(
        default="Registered",
        max_length=50
    )

    attended: bool = False


class ConferenceParticipantResponse(
    ConferenceParticipantCreate
):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    conference_id: int

    created_at: datetime


class ConferenceStatsResponse(BaseModel):

    total_conferences: int

    upcoming: int

    completed: int

    cancelled: int

    total_participants: int