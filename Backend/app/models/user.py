from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.institution import Institution


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String(30), nullable=False, default="Researcher")
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    institution = Column(String(200), nullable=True)
    department = Column(String(150), nullable=True)
    bio = Column(Text, nullable=True)
    research_interests = Column(JSON, nullable=False, default=list)
    skills = Column(JSON, nullable=False, default=list)
    profile_picture = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    approval_status = Column(String(20), nullable=False, default="Pending", index=True)
    email_verified = Column(Boolean, nullable=False, default=False, index=True)
    verification_code_hash = Column(String(128), nullable=True)
    verification_code_expires_at = Column(DateTime(timezone=True), nullable=True)
    verification_code_sent_at = Column(DateTime(timezone=True), nullable=True)
    verification_attempts = Column(Integer, nullable=False, default=0)
    password_reset_code_hash = Column(String(128), nullable=True)
    password_reset_code_expires_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_code_sent_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    institution_record = relationship("Institution", foreign_keys=[institution_id])
