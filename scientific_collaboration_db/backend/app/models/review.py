import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class PublicationReview(Base):
    """
    A reviewer assignment on a publication, created by a System Admin or an
    Institution Admin, and worked by the assigned Reviewer. This is what
    actually powers the Reviewer's "Review queue" and the Admin/Institution
    Admin's ability to hand out and track reviews — it's not just a status
    flag on Publication, so a full history of who reviewed what (and what
    they decided) is kept even after a publication moves on.
    """

    __tablename__ = "publication_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    publication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status"), nullable=False, default=ReviewStatus.PENDING
    )
    note: Mapped[str | None] = mapped_column(Text)          # instructions left by whoever assigned the review
    comments: Mapped[str | None] = mapped_column(Text)       # the reviewer's write-up / decision comments

    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    publication: Mapped["Publication"] = relationship(back_populates="reviews")
    reviewer: Mapped["User"] = relationship(back_populates="reviews_assigned", foreign_keys=[reviewer_id])
    assigned_by: Mapped["User"] = relationship(foreign_keys=[assigned_by_id])

    def __repr__(self) -> str:
        return f"<PublicationReview pub={self.publication_id} reviewer={self.reviewer_id} status={self.status}>"
