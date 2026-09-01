from sqlalchemy import Column, Integer, JSON, String, Text
from app.core.database import Base

class Institution(Base):
    __tablename__="institutions"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(200),unique=True,nullable=False,index=True)
    short_name=Column(String(30),nullable=False)
    location=Column(String(200),nullable=False,index=True)
    description=Column(Text,nullable=True)
    research_areas=Column(JSON,nullable=False,default=list)
    website=Column(String(500),nullable=True)
    source=Column(String(60),nullable=True,index=True)
    source_id=Column(String(120),nullable=True,unique=True,index=True)
    source_url=Column(String(500),nullable=True)
