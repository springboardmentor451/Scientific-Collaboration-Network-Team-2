from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    description: str = Field(min_length=2, max_length=5000)
    research_area: str = Field(min_length=2, max_length=200)
    status: str = Field(default="Active", max_length=30)
    start_date: datetime | None = None
    end_date: datetime | None = None

class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=300)
    description: str | None = Field(default=None, min_length=2, max_length=5000)
    research_area: str | None = Field(default=None, min_length=2, max_length=200)
    status: str | None = Field(default=None, max_length=30)
    start_date: datetime | None = None
    end_date: datetime | None = None

class ProjectResponse(ProjectCreate):
    id: int
    owner_id: int
    researcher_ids: list[int] = Field(default_factory=list)
    member_count: int = 0
    model_config = ConfigDict(from_attributes=True)
