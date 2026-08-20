from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class InstitutionBase(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None

class InstitutionCreate(InstitutionBase):
    name: str

class InstitutionUpdate(InstitutionBase):
    pass

class InstitutionInDBBase(InstitutionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InstitutionOut(InstitutionInDBBase):
    pass
