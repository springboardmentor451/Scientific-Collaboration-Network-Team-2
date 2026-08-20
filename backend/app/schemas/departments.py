from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DepartmentBase(BaseModel):
    institution_id: Optional[int] = None
    name: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    institution_id: int
    name: str

class DepartmentUpdate(DepartmentBase):
    pass

class DepartmentInDBBase(DepartmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DepartmentOut(DepartmentInDBBase):
    pass
