from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func

from backend.app.database.base import Base


class ResearcherInterest(Base):
    __tablename__ = "researcher_interests"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    researcher_id = Column(
        Integer,
        ForeignKey("researchers.id"),
        nullable=False
    )

    interest_id = Column(
        Integer,
        ForeignKey("research_interests.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )