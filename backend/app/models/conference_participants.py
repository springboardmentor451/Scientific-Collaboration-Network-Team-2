from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func

from backend.app.database.base import Base


class ConferenceParticipant(Base):
    __tablename__ = "conference_participants"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    conference_id = Column(
        Integer,
        ForeignKey("conferences.id"),
        nullable=False
    )

    researcher_id = Column(
        Integer,
        ForeignKey("researchers.id"),
        nullable=False
    )

    participation_type = Column(
        String(100),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )