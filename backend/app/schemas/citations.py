from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class CitationBase(BaseModel):
    citing_publication_id: Optional[int] = None
    cited_publication_id: Optional[int] = None
    external_reference_text: Optional[str] = None
    doi: Optional[str] = None

class CitationCreate(BaseModel):
    citing_publication_id: int
    cited_publication_id: Optional[int] = None
    external_reference_text: Optional[str] = None
    doi: Optional[str] = None

class CitationUpdate(BaseModel):
    cited_publication_id: Optional[int] = None
    external_reference_text: Optional[str] = None
    doi: Optional[str] = None

class CitationInDBBase(CitationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CitationOut(CitationInDBBase):
    pass
