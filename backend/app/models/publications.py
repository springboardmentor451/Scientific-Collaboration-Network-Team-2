from datetime import datetime, date
import enum
from sqlalchemy import String, Text, DateTime, Date, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

class PublicationType(str, enum.Enum):
    journal_paper = "journal_paper"
    conference_paper = "conference_paper"
    book = "book"
    patent = "patent"
    technical_report = "technical_report"
    other = "other"

class PublicationStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    published = "published"
    archived = "archived"

class Publication(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=True)
    type: Mapped[PublicationType] = mapped_column(Enum(PublicationType), nullable=False, default=PublicationType.journal_paper)
    status: Mapped[PublicationStatus] = mapped_column(Enum(PublicationStatus), nullable=False, default=PublicationStatus.draft, index=True)
    doi: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=True)
    venue: Mapped[str] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[date] = mapped_column(Date, index=True, nullable=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("researcher.id", ondelete="SET NULL"), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    creator = relationship("Researcher", backref="created_publications")
    authors = relationship("Researcher", secondary="publication_author", back_populates="publications", viewonly=True)
