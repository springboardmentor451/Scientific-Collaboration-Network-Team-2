from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.projects import ProjectStatus

class ProjectBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    funding_source: Optional[str] = None
    funding_amount: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProjectStatus] = ProjectStatus.proposed
    institution_id: Optional[int] = None

class ProjectCreate(ProjectBase):
    title: str

class ProjectUpdate(ProjectBase):
    pass

class ProjectInDBBase(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectOut(ProjectInDBBase):
    pass
