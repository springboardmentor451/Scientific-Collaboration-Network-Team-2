from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

class AdminUserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    institution: str | None
    department: str | None
    is_active: bool
    approval_status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserStatusUpdate(BaseModel):
    is_active: bool

class UserRoleUpdate(BaseModel):
    role: Literal["System Admin", "Institution Admin", "Researcher", "Reviewer", "Publisher", "Admin", "Faculty", "Student", "Collaborator"]

class UserApprovalUpdate(BaseModel):
    approval_status: Literal["Approved", "Rejected", "Pending"]

class AuditResponse(BaseModel):
    id: int
    actor_id: int | None
    actor_name: str
    action: str
    target_type: str | None
    target_id: int | None
    details: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
