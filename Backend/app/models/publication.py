from sqlalchemy import Column, ForeignKey, Integer, String, Text, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

publication_authors = Table(
    "publication_authors", Base.metadata,
    Column("publication_id", ForeignKey("publications.id", ondelete="CASCADE"), primary_key=True),
    Column("researcher_id", ForeignKey("researchers.id", ondelete="CASCADE"), primary_key=True),
)


class Publication(Base):
    __tablename__ = "publications"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(300), nullable=False, index=True)
    authors = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=True)
    research_area = Column(String(200), nullable=False, index=True)
    venue = Column(String(250), nullable=False)
    publication_year = Column(Integer, nullable=False)
    doi_url = Column(String(500), nullable=True)
    publication_type = Column(String(80), nullable=False, default="Journal Article")
    status = Column(String(20), nullable=False, default="Draft", index=True)
    document_path = Column(String(500), nullable=True)
    owner = relationship("User")
    researcher_authors = relationship("Researcher", secondary=publication_authors)

    @property
    def owner_name(self):
        return self.owner.full_name
