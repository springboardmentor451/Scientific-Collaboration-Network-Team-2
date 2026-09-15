import uuid

from pydantic import BaseModel

from app.models.conference import ParticipationRole


class ParticipationCreate(BaseModel):
    conference_id: uuid.UUID
    researcher_id: uuid.UUID | None = None  # defaults to the submitter if omitted
    publication_id: uuid.UUID | None = None
    role: ParticipationRole = ParticipationRole.ATTENDEE
    presentation_title: str | None = None


class ParticipationUpdate(BaseModel):
    role: ParticipationRole | None = None
    presentation_title: str | None = None
    publication_id: uuid.UUID | None = None