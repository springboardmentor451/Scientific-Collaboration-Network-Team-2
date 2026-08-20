from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

class Reference(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    publication_id: Mapped[int] = mapped_column(ForeignKey("publication.id", ondelete="CASCADE"), index=True, nullable=False)
    reference_text: Mapped[str] = mapped_column(Text, nullable=False)
    doi: Mapped[str] = mapped_column(String(100), index=True, nullable=True)
    external_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationships
    publication = relationship("Publication", backref="references")
