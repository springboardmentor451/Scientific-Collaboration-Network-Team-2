import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PublicationType(str, enum.Enum):
    JOURNAL_PAPER = "journal_paper"
    CONFERENCE_PAPER = "conference_paper"
    BOOK = "book"
    PATENT = "patent"
    TECHNICAL_REPORT = "technical_report"
    OTHER = "other"


class PublicationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Publication(Base):
    """A journal paper, conference paper, book, patent, or report."""

    __tablename__ = "publications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    abstract: Mapped[str | None] = mapped_column(Text)

    publication_type: Mapped[PublicationType] = mapped_column(
        Enum(PublicationType, name="publication_type"), nullable=False
    )
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, name="publication_status"), nullable=False, default=PublicationStatus.DRAFT
    )

    doi: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    journal_or_venue: Mapped[str | None] = mapped_column(String(255))
    volume: Mapped[str | None] = mapped_column(String(50))
    issue: Mapped[str | None] = mapped_column(String(50))
    pages: Mapped[str | None] = mapped_column(String(50))
    publication_date: Mapped[date | None] = mapped_column(Date)
    file_path: Mapped[str | None] = mapped_column(String(500))  # local path or S3 key

    # A publication may optionally arise from a funded project
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="publications")
    authors: Mapped[list["PublicationAuthor"]] = relationship(
        back_populates="publication", cascade="all, delete-orphan", order_by="PublicationAuthor.author_order"
    )
    conference_participations: Mapped[list["ConferenceParticipation"]] = relationship(back_populates="publication")

    citations_made: Mapped[list["Citation"]] = relationship(
        back_populates="citing_publication",
        foreign_keys="Citation.citing_publication_id",
        cascade="all, delete-orphan",
    )
    citations_received: Mapped[list["Citation"]] = relationship(
        back_populates="cited_publication",
        foreign_keys="Citation.cited_publication_id",
    )

    def __repr__(self) -> str:
        return f"<Publication {self.title[:40]!r}>"

    @property
    def file_name(self) -> str | None:
        if not self.file_path:
            return None
        return self.file_path.replace("\\", "/").rsplit("/", 1)[-1]

    @property
    def author_names(self) -> list[str]:
        # Derived from the publication_authors association (already ordered
        # by author_order via the `authors` relationship). This is what
        # actually feeds PublicationOut.author_names — without it, that
        # field silently falls back to its Pydantic default of [] for
        # every publication, since "author_names" isn't a real column.
        return [link.researcher.full_name for link in self.authors if link.researcher]


class PublicationAuthor(Base):
    """
    Association object linking Researcher <-> Publication (co-authorship).
    Carries extra metadata: author order and corresponding-author flag.
    """

    __tablename__ = "publication_authors"

    publication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publications.id", ondelete="CASCADE"), primary_key=True
    )
    researcher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("researchers.id", ondelete="CASCADE"), primary_key=True
    )
    author_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_corresponding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    publication: Mapped["Publication"] = relationship(back_populates="authors")
    researcher: Mapped["Researcher"] = relationship(back_populates="publication_links")

    def __repr__(self) -> str:
        return f"<PublicationAuthor pub={self.publication_id} researcher={self.researcher_id}>"
