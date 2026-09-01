from datetime import datetime
from sqlalchemy import Boolean,Column,DateTime,ForeignKey,Integer,String,Table,Text
from sqlalchemy.orm import relationship
from app.core.database import Base

conference_participants=Table("conference_participants",Base.metadata,Column("conference_id",ForeignKey("conferences.id",ondelete="CASCADE"),primary_key=True),Column("user_id",ForeignKey("users.id",ondelete="CASCADE"),primary_key=True))
class Conference(Base):
    __tablename__="conferences"
    id=Column(Integer,primary_key=True,index=True)
    title=Column(String(300),nullable=False,index=True)
    topic=Column(String(250),nullable=False,index=True)
    description=Column(Text,nullable=True)
    location=Column(String(200),nullable=False,index=True)
    starts_at=Column(DateTime(timezone=True),nullable=False,index=True)
    ends_at=Column(DateTime(timezone=True),nullable=True)
    registration_url=Column(String(500),nullable=True)
    is_open=Column(Boolean,nullable=False,default=True)
    participants=relationship("User",secondary=conference_participants)
