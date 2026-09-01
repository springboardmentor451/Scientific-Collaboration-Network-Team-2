from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class CitationCreate(BaseModel):
    publication_id: int | None = None
    cited_title: str = Field(min_length=2, max_length=300)
    cited_authors: str | None = Field(default=None, max_length=500)
    cited_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)

class CitationUpdate(BaseModel):
    publication_id: int | None = None
    cited_title: str | None = Field(default=None, min_length=2, max_length=300)
    cited_authors: str | None = Field(default=None, max_length=500)
    cited_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)

class CitationResponse(CitationCreate):
    id: int
    owner_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
