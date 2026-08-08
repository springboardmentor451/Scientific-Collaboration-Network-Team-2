from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.database.base import Base


class Funding(Base):
    __tablename__ = "funding"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    funding_source = Column(
        String(255),
        nullable=False
    )

    amount = Column(
        Numeric(15, 2),
        nullable=True
    )

    currency = Column(
        String(10),
        default="INR"
    )

    grant_number = Column(
        String(100),
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

    description = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    