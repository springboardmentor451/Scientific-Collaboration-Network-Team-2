import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    Table,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class ProjectStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


# Team membership: which researchers work on which project, and in what role.
project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("research_projects.id"), primary_key=True),
    Column("researcher_id", Integer, ForeignKey("researchers.id"), primary_key=True),
    Column("role_in_project", String, nullable=True),
)

# Institutional collaboration: which institutions are partners on a project.
project_institutions = Table(
    "project_institutions",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("research_projects.id"), primary_key=True),
    Column("institution_id", Integer, ForeignKey("institutions.id"), primary_key=True),
)


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNED, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    funding_agency = Column(String, nullable=True)
    funding_amount = Column(Float, nullable=True)

    members = relationship(
        "Researcher", secondary=project_members, backref="projects"
    )
    institutions = relationship(
        "Institution", secondary=project_institutions, backref="collaborative_projects"
    )
