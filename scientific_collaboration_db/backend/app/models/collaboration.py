import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CollaborationType(str, enum.Enum):
    CO_AUTHORSHIP = "co_authorship"
    JOINT_PROJECT = "joint_project"
    INSTITUTIONAL_PARTNERSHIP = "institutional_partnership"
    OTHER = "other"


class Collaboration(Base):
    """
    A recorded collaboration link, typically between two institutions,
    optionally tied to the project that generated it.
    """

    __tablename__ = "collaborations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collaboration_type: Mapped[CollaborationType] = mapped_column(
        Enum(CollaborationType, name="collaboration_type"), nullable=False
    )

    institution_a_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE")
    )
    institution_b_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE")
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL")
    )

    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    institution_a: Mapped["Institution"] = relationship(foreign_keys=[institution_a_id])
    institution_b: Mapped["Institution"] = relationship(foreign_keys=[institution_b_id])
    project: Mapped["Project"] = relationship(back_populates="collaborations")

    def __repr__(self) -> str:
        return f"<Collaboration {self.collaboration_type} {self.institution_a_id}<->{self.institution_b_id}>"
