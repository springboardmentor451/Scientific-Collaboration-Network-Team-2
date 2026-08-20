from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ProjectAssignmentBase(BaseModel):
    project_id: Optional[int] = None
    researcher_id: Optional[int] = None
    role_in_project: Optional[str] = "member"

class ProjectAssignmentCreate(ProjectAssignmentBase):
    project_id: int
    researcher_id: int

class ProjectAssignmentUpdate(BaseModel):
    role_in_project: Optional[str] = None

class ProjectAssignmentInDBBase(ProjectAssignmentBase):
    id: int
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectAssignmentOut(ProjectAssignmentInDBBase):
    pass
