import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Institution(Base):
    """University, research institute, lab, or funding organization."""

    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(255))
    institution_type: Mapped[str | None] = mapped_column(String(100))  # university, lab, publisher, funding body...

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    researchers: Mapped[list["Researcher"]] = relationship(back_populates="institution")
    projects: Mapped[list["Project"]] = relationship(back_populates="lead_institution")
    # Staff accounts (institution_admin / reviewer) attached directly to this
    # institution via User.institution_id, rather than through a Researcher profile.
    staff: Mapped[list["User"]] = relationship(back_populates="institution", foreign_keys="User.institution_id")

    def __repr__(self) -> str:
        return f"<Institution {self.name}>"
