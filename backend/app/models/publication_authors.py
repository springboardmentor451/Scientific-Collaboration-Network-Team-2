from sqlalchemy import ForeignKey, Boolean, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

class PublicationAuthor(Base):
    __tablename__ = "publication_author"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    publication_id: Mapped[int] = mapped_column(ForeignKey("publication.id", ondelete="CASCADE"), index=True, nullable=False)
    researcher_id: Mapped[int] = mapped_column(ForeignKey("researcher.id", ondelete="CASCADE"), index=True, nullable=False)
    author_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_corresponding_author: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    publication = relationship("Publication", backref="author_relations")
    researcher = relationship("Researcher", backref="publication_relations")

    __table_args__ = (
        UniqueConstraint("publication_id", "researcher_id", name="uq_pub_res"),
    )

# Add relation in Researcher dynamically or import it.
from backend.app.models.researchers import Researcher
Researcher.publications = relationship(
    "Publication",
    secondary="publication_author",
    back_populates="authors",
    overlaps="author_relations,publication,publication_relations,researcher"
)
