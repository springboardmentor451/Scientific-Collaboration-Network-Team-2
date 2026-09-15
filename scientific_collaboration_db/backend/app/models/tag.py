import enum
import uuid

from sqlalchemy import Column, Enum, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TagCategory(str, enum.Enum):
    SKILL = "skill"
    RESEARCH_INTEREST = "research_interest"


# Many-to-many: a researcher can have many skills/interests, a tag can belong to many researchers
researcher_tags = Table(
    "researcher_tags",
    Base.metadata,
    Column("researcher_id", UUID(as_uuid=True), ForeignKey("researchers.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    """A skill or research-interest keyword, reusable across researchers."""

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("name", "category", name="uq_tag_name_category"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[TagCategory] = mapped_column(Enum(TagCategory, name="tag_category"), nullable=False)

    researchers: Mapped[list["Researcher"]] = relationship(secondary=researcher_tags, back_populates="tags")

    def __repr__(self) -> str:
        return f"<Tag {self.name} ({self.category})>"
