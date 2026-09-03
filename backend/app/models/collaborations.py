from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship

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
        ForeignKey(
            "researchers.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    researcher_id_2 = Column(
        Integer,
        ForeignKey(
            "researchers.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    collaboration_type = Column(
        String(100),
        nullable=True,
        index=True
    )

    description = Column(
        Text,
        nullable=True
    )

    start_date = Column(
        Date,
        nullable=True,
        index=True
    )

    end_date = Column(
        Date,
        nullable=True
    )

    status = Column(
        String(50),
        nullable=True,
        default="Pending",
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc)
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    researcher_1 = relationship(
        "Researcher",
        foreign_keys=[researcher_id_1]
    )

    researcher_2 = relationship(
        "Researcher",
        foreign_keys=[researcher_id_2]
    )