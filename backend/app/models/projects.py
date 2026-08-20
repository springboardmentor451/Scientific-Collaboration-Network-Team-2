from datetime import datetime, date
import enum
from sqlalchemy import String, Text, DateTime, Date, ForeignKey, Numeric, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

class ProjectStatus(str, enum.Enum):
    proposed = "proposed"
    active = "active"
    completed = "completed"
    on_hold = "on_hold"

class Project(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    funding_source: Mapped[str] = mapped_column(String(255), nullable=True)
    funding_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.proposed, index=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institution.id", ondelete="SET NULL"), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    institution = relationship("Institution", backref="projects")
    researchers = relationship("Researcher", secondary="project_assignment", back_populates="projects", viewonly=True)
