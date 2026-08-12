from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.database.base import Base


class InstitutionPartnership(Base):
    __tablename__ = "institution_partnerships"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    institution_id_1 = Column(
        Integer,
        ForeignKey("institutions.id"),
        nullable=False
    )

    institution_id_2 = Column(
        Integer,
        ForeignKey("institutions.id"),
        nullable=False
    )

    partnership_type = Column(
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