from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.database.base import Base


class Collaboration(Base):
    __tablename__ = "collaborations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    researcher_id_1 = Column(
        Integer,
        ForeignKey("researchers.id"),
        nullable=False
    )

    researcher_id_2 = Column(
        Integer,
        ForeignKey("researchers.id"),
        nullable=False
    )

    collaboration_type = Column(
        String(100),
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    start_date = Column(
        Date,
        nullable=True
    )

    end_date = Column(
        Date,
        nullable=True
    )

    status = Column(
        String(50),
        default="active"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )