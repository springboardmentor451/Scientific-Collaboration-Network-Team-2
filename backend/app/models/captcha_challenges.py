from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from backend.app.database.base import Base


class CaptchaChallenge(Base):
    __tablename__ = "captcha_challenges"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(String(64), nullable=False, unique=True, index=True)
    answer_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    verified = Column(Boolean, nullable=False, default=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False)