from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

class Citation(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    citing_publication_id: Mapped[int] = mapped_column(ForeignKey("publication.id", ondelete="CASCADE"), index=True, nullable=False)
    cited_publication_id: Mapped[int] = mapped_column(ForeignKey("publication.id", ondelete="SET NULL"), index=True, nullable=True)
    external_reference_text: Mapped[str] = mapped_column(Text, nullable=True)
    doi: Mapped[str] = mapped_column(String(100), index=True, nullable=True)  # DOI of cited paper if external
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    citing_publication = relationship("Publication", foreign_keys=[citing_publication_id], backref="citations_made")
    cited_publication = relationship("Publication", foreign_keys=[cited_publication_id], backref="citations_received")
