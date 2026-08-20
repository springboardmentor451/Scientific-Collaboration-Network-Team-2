import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Enum, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    non_binary = "non_binary"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"

class Researcher(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institution.id", ondelete="SET NULL"), index=True, nullable=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("department.id", ondelete="SET NULL"), index=True, nullable=True)
    
    # Demographics
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), default=GenderEnum.prefer_not_to_say, nullable=True)
    gender_other: Mapped[str] = mapped_column(String(255), nullable=True)
    nationality: Mapped[str] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    mobile_number: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Academic & Professional
    designation: Mapped[str] = mapped_column(String(150), nullable=True)
    highest_qualification: Mapped[str] = mapped_column(String(150), nullable=True)
    year_highest_qualification: Mapped[int] = mapped_column(Integer, nullable=True)

    # External IDs
    orcid_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=True)
    google_scholar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    researchgate_url: Mapped[str] = mapped_column(String(500), nullable=True)
    scopus_id: Mapped[str] = mapped_column(String(100), nullable=True)
    wos_id: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Store lists as JSON
    research_interests: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    skills: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    
    affiliations: Mapped[str] = mapped_column(Text, nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    profile_photo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="researcher_profile", uselist=False)
    institution = relationship("Institution", backref="researchers")
    department = relationship("Department", backref="researchers")

    @property
    def institution_name(self) -> Optional[str]:
        return self.institution.name if self.institution else None

    @property
    def department_name(self) -> Optional[str]:
        return self.department.name if self.department else None
