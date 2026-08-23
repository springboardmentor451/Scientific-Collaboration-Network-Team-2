from sqlalchemy import Column, Integer, String, DateTime, func

from app.db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False, index=True)
    status_code = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True, index=True)
    user_role = Column(String, nullable=True)
    client_ip = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)
