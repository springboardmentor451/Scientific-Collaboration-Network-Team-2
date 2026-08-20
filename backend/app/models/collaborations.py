from datetime import datetime
import enum
from sqlalchemy import String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

class CollaborationType(str, enum.Enum):
    co_authorship = "co_authorship"
    project = "project"
    institutional = "institutional"

class Collaboration(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    collaboration_type: Mapped[CollaborationType] = mapped_column(Enum(CollaborationType), nullable=False, index=True)
    researcher_id_1: Mapped[int] = mapped_column(ForeignKey("researcher.id", ondelete="CASCADE"), index=True, nullable=False)
    researcher_id_2: Mapped[int] = mapped_column(ForeignKey("researcher.id", ondelete="CASCADE"), index=True, nullable=True)
    institution_id_1: Mapped[int] = mapped_column(ForeignKey("institution.id", ondelete="CASCADE"), index=True, nullable=True)
    institution_id_2: Mapped[int] = mapped_column(ForeignKey("institution.id", ondelete="CASCADE"), index=True, nullable=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="SET NULL"), index=True, nullable=True)
    publication_id: Mapped[int] = mapped_column(ForeignKey("publication.id", ondelete="SET NULL"), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    researcher_1 = relationship("Researcher", foreign_keys=[researcher_id_1], backref="collaborations_as_1")
    researcher_2 = relationship("Researcher", foreign_keys=[researcher_id_2], backref="collaborations_as_2")
    institution_1 = relationship("Institution", foreign_keys=[institution_id_1], backref="collaborations_as_1")
    institution_2 = relationship("Institution", foreign_keys=[institution_id_2], backref="collaborations_as_2")
    project = relationship("Project", backref="collaborations")
    publication = relationship("Publication", backref="collaborations")
