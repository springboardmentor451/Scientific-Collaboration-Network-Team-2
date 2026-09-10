import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    RESEARCHER = "researcher"
    INSTITUTION_ADMIN = "institution_admin"
    REVIEWER = "reviewer"
    SYSTEM_ADMIN = "system_admin"


class User(Base):
    """Login / account record. A Researcher profile links back to a User."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.RESEARCHER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Home institution for staff accounts that don't have a Researcher profile
    # (institution_admin, reviewer). Lets an Institution Admin be scoped to
    # "their" institution, and a Reviewer be matched up with the institution
    # that assigned them, without forcing every staff account to also carry
    # a full academic Researcher profile. Researcher accounts keep using
    # Researcher.institution_id as their source of truth instead (see
    # User.effective_institution_id below).
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    researcher: Mapped["Researcher"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
    institution: Mapped["Institution"] = relationship(back_populates="staff", foreign_keys=[institution_id])
    reviews_assigned: Mapped[list["PublicationReview"]] = relationship(
        back_populates="reviewer", foreign_keys="PublicationReview.reviewer_id", cascade="all, delete-orphan"
    )

    @property
    def effective_institution_id(self):
        """
        The institution this user is actually scoped to. Which source wins
        depends on role, not just "whichever is set" — a Researcher who gets
        promoted to Institution Admin (or Reviewer) keeps their old Researcher
        profile around (nothing deletes it), so if we didn't check role here,
        their stale researcher institution would silently override whatever
        institution an admin just explicitly assigned via User.institution_id.
        """
        if self.role == UserRole.RESEARCHER:
            return self.researcher.institution_id if self.researcher else None
        return self.institution_id

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
