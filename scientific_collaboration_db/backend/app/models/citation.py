import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Citation(Base):
    """
    A citation record: one publication in the system citing another.
    Also supports citing an external work (not in the database) via the
    external_* fields, so reference lists aren't limited to internal publications.
    """

    __tablename__ = "citations"
    __table_args__ = (
        CheckConstraint(
            "cited_publication_id IS NOT NULL OR external_title IS NOT NULL",
            name="ck_citation_has_target",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    citing_publication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publications.id", ondelete="CASCADE"), nullable=False
    )
    # Nullable: citation may point outside the system (external_* fields used instead)
    cited_publication_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publications.id", ondelete="CASCADE")
    )

    external_title: Mapped[str | None] = mapped_column(String(500))
    external_doi: Mapped[str | None] = mapped_column(String(255))
    external_authors: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    citing_publication: Mapped["Publication"] = relationship(
        back_populates="citations_made", foreign_keys=[citing_publication_id]
    )
    cited_publication: Mapped["Publication"] = relationship(
        back_populates="citations_received", foreign_keys=[cited_publication_id]
    )

    def __repr__(self) -> str:
        target = self.cited_publication_id or self.external_title
        return f"<Citation {self.citing_publication_id} -> {target}>"
