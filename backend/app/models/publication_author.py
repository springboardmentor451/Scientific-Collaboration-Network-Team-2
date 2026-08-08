from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func

from backend.app.database.base import Base


class PublicationAuthor(Base):
    __tablename__ = "publication_authors"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    publication_id = Column(
        Integer,
        ForeignKey("publications.id"),
        nullable=False
    )

    researcher_id = Column(
        Integer,
        ForeignKey("researchers.id"),
        nullable=False
    )

    author_order = Column(
        Integer,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )