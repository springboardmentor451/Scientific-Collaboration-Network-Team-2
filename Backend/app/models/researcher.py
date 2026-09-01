from sqlalchemy import Column, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.institution import Institution


class Researcher(Base):
    __tablename__ = "researchers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    department = Column(String(150), nullable=False)
    institution = Column(String(200), nullable=False, index=True)
    field = Column(String(200), nullable=False)
    skills = Column(JSON, nullable=False, default=list)
    research_interests = Column(JSON, nullable=False, default=list)
    affiliation = Column(String(200), nullable=True)
    publication_count = Column(Integer, nullable=False, default=0)
    collaboration_count = Column(Integer, nullable=False, default=0)
    source = Column(String(60), nullable=True, index=True)
    source_id = Column(String(120), nullable=True, unique=True, index=True)
    source_url = Column(String(500), nullable=True)
    user = relationship("User")
    institution_record = relationship("Institution", foreign_keys=[institution_id])
