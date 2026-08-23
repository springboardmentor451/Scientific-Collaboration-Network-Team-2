from pydantic import BaseModel, EmailStr
from typing import Optional

class ResearcherBase(BaseModel):
    name: str
    email: EmailStr
    department: Optional[str] = None
    designation: Optional[str] = None
    
class ResearcherCreate(ResearcherBase):
    pass

class ResearcherOut(ResearcherBase):
    id: int
    
    class Config:
        from_attributes = True
        
class ResearcherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    designation: Optional[str] = None