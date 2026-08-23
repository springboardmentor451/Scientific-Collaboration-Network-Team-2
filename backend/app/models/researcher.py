from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.publication import publication_authors
from app.db.database import Base


class Researcher(Base):
    __tablename__ = "researchers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    department = Column(String)
    designation = Column(String)
    institution_id = Column(Integer, ForeignKey("institutions.id"))

    institution = relationship("Institution", back_populates="researchers")
    publications = relationship("Publication", secondary=publication_authors, back_populates="authors")