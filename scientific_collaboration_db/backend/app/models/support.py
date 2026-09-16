import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SupportMessage(Base):
    """
    A single message in a Researcher/Reviewer/Institution Admin's direct
    support conversation with the System Admin team.

    Every message in a conversation shares the same thread_user_id — the
    non-admin account the thread belongs to — regardless of whether the
    message was actually typed by that user or by a System Admin replying
    to them. That keeps "my conversation with support" a single simple
    query (WHERE thread_user_id = me) for everyone except System Admins,
    who instead browse every thread via GET /support/threads.
    """

    __tablename__ = "support_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_from_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # "Read by the other side of the conversation" — read_by_admin for a
    # user-authored message, read_by_user for an admin-authored one. A
    # single flag suffices because a message only ever needs to track
    # whether its one recipient side has seen it.
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    thread_user: Mapped["User"] = relationship(foreign_keys=[thread_user_id])
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])

    def __repr__(self) -> str:
        return f"<SupportMessage thread={self.thread_user_id} from_admin={self.is_from_admin}>"
