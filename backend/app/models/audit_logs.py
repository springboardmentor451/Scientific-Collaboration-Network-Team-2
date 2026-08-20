from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, JSON, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., create, update, delete, login
    entity_type: Mapped[str] = mapped_column(String(100), nullable=True)  # e.g., publication, researcher
    entity_id: Mapped[int] = mapped_column(Integer, index=True, nullable=True)  # Generic entity PK
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="audit_logs")
