from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Citation(Base):
    """
    Represents one reference made by a publication.

    If the cited work is also tracked in this system, cited_publication_id
    is set and the citation can be used to compute in-system citation counts.
    Otherwise (citing an external paper/book), external_reference/doi hold
    the free-text reference and its DOI, if any.
    """

    __tablename__ = "citations"

    id = Column(Integer, primary_key=True, index=True)
    citing_publication_id = Column(Integer, ForeignKey("publications.id"), nullable=False)
    cited_publication_id = Column(Integer, ForeignKey("publications.id"), nullable=True)
    external_reference = Column(String, nullable=True)
    doi = Column(String, nullable=True)

    citing_publication = relationship(
        "Publication", foreign_keys=[citing_publication_id]
    )
    cited_publication = relationship(
        "Publication", foreign_keys=[cited_publication_id]
    )
