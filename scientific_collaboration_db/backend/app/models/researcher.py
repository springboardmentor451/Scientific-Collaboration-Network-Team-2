import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.tag import researcher_tags


class Researcher(Base):
    """Academic profile, one-to-one with a User account."""

    __tablename__ = "researchers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="SET NULL")
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(150))
    academic_title: Mapped[str | None] = mapped_column(String(100))  # e.g. Professor, PhD Candidate
    orcid_id: Mapped[str | None] = mapped_column(String(25), unique=True)
    bio: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="researcher")
    institution: Mapped["Institution"] = relationship(back_populates="researchers")
    tags: Mapped[list["Tag"]] = relationship(secondary=researcher_tags, back_populates="researchers")

    publication_links: Mapped[list["PublicationAuthor"]] = relationship(back_populates="researcher")
    project_memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="researcher")
    conference_participations: Mapped[list["ConferenceParticipation"]] = relationship(back_populates="researcher")

    def __repr__(self) -> str:
        return f"<Researcher {self.full_name}>"
