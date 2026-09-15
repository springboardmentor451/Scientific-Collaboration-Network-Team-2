import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ParticipationRole(str, enum.Enum):
    PRESENTER = "presenter"
    ATTENDEE = "attendee"
    ORGANIZER = "organizer"
    REVIEWER = "reviewer"


class Conference(Base):
    """A conference / academic event."""

    __tablename__ = "conferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    participations: Mapped[list["ConferenceParticipation"]] = relationship(
        back_populates="conference", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conference {self.name}>"


class ConferenceParticipation(Base):
    """A researcher's participation record at a conference (registration, presentation, etc)."""

    __tablename__ = "conference_participations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conferences.id", ondelete="CASCADE"), nullable=False
    )
    researcher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("researchers.id", ondelete="CASCADE"), nullable=False
    )
    publication_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publications.id", ondelete="SET NULL")
    )
    role: Mapped[ParticipationRole] = mapped_column(
        Enum(ParticipationRole, name="participation_role"), nullable=False, default=ParticipationRole.ATTENDEE
    )
    presentation_title: Mapped[str | None] = mapped_column(String(500))
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conference: Mapped["Conference"] = relationship(back_populates="participations")
    researcher: Mapped["Researcher"] = relationship(back_populates="conference_participations")
    publication: Mapped["Publication"] = relationship(back_populates="conference_participations")

    def __repr__(self) -> str:
        return f"<ConferenceParticipation conf={self.conference_id} researcher={self.researcher_id}>"
