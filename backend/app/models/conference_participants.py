from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship

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
        ForeignKey(
            "conferences.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    researcher_id = Column(
        Integer,
        ForeignKey(
            "researchers.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    role = Column(
        String(100),
        nullable=True
    )

    registration_status = Column(
        String(50),
        nullable=False,
        default="Registered"
    )

    attended = Column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    conference = relationship(
        "Conference",
        back_populates="participants"
    )

    researcher = relationship(
        "Researcher"
    )