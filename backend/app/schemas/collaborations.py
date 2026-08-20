from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.collaborations import CollaborationType

class CollaborationBase(BaseModel):
    collaboration_type: Optional[CollaborationType] = None
    researcher_id_1: Optional[int] = None
    researcher_id_2: Optional[int] = None
    institution_id_1: Optional[int] = None
    institution_id_2: Optional[int] = None
    project_id: Optional[int] = None
    publication_id: Optional[int] = None

class CollaborationCreate(CollaborationBase):
    collaboration_type: CollaborationType
    researcher_id_1: int

class CollaborationUpdate(CollaborationBase):
    pass

class CollaborationInDBBase(CollaborationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CollaborationOut(CollaborationInDBBase):
    pass
