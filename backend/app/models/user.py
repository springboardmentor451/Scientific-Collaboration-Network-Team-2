import enum

from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class UserRole(str, enum.Enum):
    RESEARCHER = "researcher"
    INSTITUTION_ADMIN = "institution_admin"
    REVIEWER = "reviewer"
    SYSTEM_ADMIN = "system_admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.RESEARCHER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Optional link to a researcher profile (a "Researcher" role user
    # generally has one; admins/reviewers may not).
    researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=True)
    # Institution this user administers / belongs to (for Institution Admins).
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)

    researcher = relationship("Researcher", foreign_keys=[researcher_id])
    institution = relationship("Institution", foreign_keys=[institution_id])
