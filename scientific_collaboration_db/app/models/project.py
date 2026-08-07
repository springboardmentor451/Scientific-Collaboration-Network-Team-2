import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(Base):
    """A funded research project / grant."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    funding_source: Mapped[str | None] = mapped_column(String(255))
    budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"), nullable=False, default=ProjectStatus.PLANNED
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)

    lead_institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="SET NULL")
    )
    lead_researcher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("researchers.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lead_institution: Mapped["Institution"] = relationship(back_populates="projects")
    lead_researcher: Mapped["Researcher"] = relationship(foreign_keys=[lead_researcher_id])
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    publications: Mapped[list["Publication"]] = relationship(back_populates="project")
    collaborations: Mapped[list["Collaboration"]] = relationship(back_populates="project")

    def __repr__(self) -> str:
        return f"<Project {self.title[:40]!r}>"


class ProjectMember(Base):
    """Association object: which researchers are assigned to which project, and their role."""

    __tablename__ = "project_members"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    researcher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("researchers.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(100), default="Contributor", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="members")
    researcher: Mapped["Researcher"] = relationship(back_populates="project_memberships")

    def __repr__(self) -> str:
        return f"<ProjectMember project={self.project_id} researcher={self.researcher_id} role={self.role}>"
