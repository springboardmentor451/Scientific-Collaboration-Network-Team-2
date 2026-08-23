import enum

from sqlalchemy import Column, Integer, String, Table, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.db.database import Base

# The association table — note this is NOT a class, just a Table object.
# It has no id of its own; it exists purely to link publications and researchers.
publication_authors = Table(
    "publication_authors",
    Base.metadata,
    Column("publication_id", Integer, ForeignKey("publications.id"), primary_key=True),
    Column("researcher_id", Integer, ForeignKey("researchers.id"), primary_key=True),
)


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
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    abstract = Column(String)
    doi = Column(String)

    # --- Added fields (spec: publication type, status, year, venue, file) ---
    # These are additive/nullable so they don't disturb any existing rows
    # or code that was already relying on the original four fields.
    publication_type = Column(
        Enum(PublicationType), default=PublicationType.OTHER, nullable=False
    )
    status = Column(Enum(PublicationStatus), default=PublicationStatus.DRAFT, nullable=False)
    year = Column(Integer, nullable=True)
    venue = Column(String, nullable=True)  # journal / conference / publisher name
    file_path = Column(String, nullable=True)  # uploaded manuscript/PDF location

    authors = relationship(
        "Researcher", secondary=publication_authors, back_populates="publications"
    )