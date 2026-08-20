from datetime import datetime, timezone
import enum
from sqlalchemy import String, DateTime, Boolean, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base_class import Base

class UserRole(str, enum.Enum):
    researcher = "researcher"
    institution_admin = "institution_admin"
    reviewer = "reviewer"
    system_admin = "system_admin"

class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.researcher)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_token: Mapped[str] = mapped_column(String(255), nullable=True)
    verification_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
