from datetime import datetime
from sqlalchemy import ForeignKey, String, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

class ProjectAssignment(Base):
    __tablename__ = "project_assignment"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True, nullable=False)
    researcher_id: Mapped[int] = mapped_column(ForeignKey("researcher.id", ondelete="CASCADE"), index=True, nullable=False)
    role_in_project: Mapped[str] = mapped_column(String(100), default="member", nullable=False)  # e.g., PI, co-PI, member
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", backref="assignments")
    researcher = relationship("Researcher", backref="project_assignments")

    __table_args__ = (
        UniqueConstraint("project_id", "researcher_id", name="uq_proj_res"),
    )

# Add relation in Researcher dynamically or import it.
from backend.app.models.researchers import Researcher
Researcher.projects = relationship(
    "Project",
    secondary="project_assignment",
    back_populates="researchers",
    overlaps="assignments,project,project_assignments,researcher"
)
