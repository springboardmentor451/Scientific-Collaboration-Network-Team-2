from datetime import datetime, date
import enum
from sqlalchemy import ForeignKey, String, DateTime, Date, Enum, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

class ParticipationRole(str, enum.Enum):
    presenter = "presenter"
    attendee = "attendee"
    organizer = "organizer"
    reviewer = "reviewer"

class ConferenceParticipation(Base):
    __tablename__ = "conference_participation"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conference_id: Mapped[int] = mapped_column(ForeignKey("conference.id", ondelete="CASCADE"), index=True, nullable=False)
    researcher_id: Mapped[int] = mapped_column(ForeignKey("researcher.id", ondelete="CASCADE"), index=True, nullable=False)
    participation_role: Mapped[ParticipationRole] = mapped_column(Enum(ParticipationRole), nullable=False, default=ParticipationRole.attendee)
    presentation_title: Mapped[str] = mapped_column(String(500), nullable=True)
    registration_date: Mapped[date] = mapped_column(Date, nullable=True)

    # Relationships
    conference = relationship("Conference", backref="participations")
    researcher = relationship("Researcher", backref="conference_participations")

    __table_args__ = (
        UniqueConstraint("conference_id", "researcher_id", name="uq_conf_res"),
    )

# Add relation in Researcher dynamically
from backend.app.models.researchers import Researcher
Researcher.conferences = relationship(
    "Conference",
    secondary="conference_participation",
    back_populates="researchers",
    overlaps="conference,conference_participations,participations,researcher"
)
