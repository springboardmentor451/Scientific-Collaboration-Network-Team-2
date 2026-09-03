from datetime import date, datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import relationship

from backend.app.database.base import Base


class Conference(Base):
    __tablename__ = "conferences"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(255),
        nullable=False,
        index=True
    )

    description = Column(
        Text,
        nullable=True
    )

    organizer = Column(
        String(255),
        nullable=True
    )

    location = Column(
        String(255),
        nullable=True,
        index=True
    )

    start_date = Column(
        Date,
        nullable=True,
        index=True
    )

    end_date = Column(
        Date,
        nullable=True,
        index=True
    )

    field = Column(
        String(150),
        nullable=True,
        index=True
    )

    website = Column(
        String(500),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    @property
    def status(self):
        today = date.today()

        if self.end_date and self.end_date < today:
            return "Completed"

        return "Upcoming"

    participants = relationship(
        "ConferenceParticipant",
        back_populates="conference",
        cascade="all, delete-orphan"
    )