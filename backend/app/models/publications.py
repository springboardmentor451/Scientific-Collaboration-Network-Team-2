from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.sql import func

from backend.app.database.base import Base


class Publication(Base):

    __tablename__ = "publications"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(500),
        nullable=False
    )

    abstract = Column(
        Text,
        nullable=True
    )

    publication_type = Column(
        String(100),
        nullable=True
    )

    journal_name = Column(
        String(255),
        nullable=True
    )

    doi = Column(
        String(255),
        unique=True,
        nullable=True
    )

    publication_date = Column(
        Date,
        nullable=True
    )

    volume = Column(
        String(50),
        nullable=True
    )

    issue = Column(
        String(50),
        nullable=True
    )

    pages = Column(
        String(50),
        nullable=True
    )

    url = Column(
        String(500),
        nullable=True
    )

    pdf_file = Column(
        String(500),
        nullable=True
    )

    citation_count = Column(
        Integer,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )