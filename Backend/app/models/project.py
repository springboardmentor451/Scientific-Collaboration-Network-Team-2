from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

project_researchers = Table(
    "project_researchers", Base.metadata,
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("researcher_id", ForeignKey("researchers.id", ondelete="CASCADE"), primary_key=True),
)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(300), nullable=False, index=True)
    description = Column(Text, nullable=False)
    research_area = Column(String(200), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="Active")
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    owner = relationship("User")
    researchers = relationship("Researcher", secondary=project_researchers)
