from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func

from backend.app.database.base import Base


class Researcher(Base):

    __tablename__ = "researchers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    institution_id = Column(
        Integer,
        ForeignKey("institutions.id"),
        nullable=True
    )

    research_area = Column(
        String(255),
        nullable=True
    )

    biography = Column(
        Text,
        nullable=True
    )

    profile_url = Column(
        String(500),
        nullable=True
    )

    status = Column(
        String(50),
        nullable=False,
        default="Active"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )