from typing import Optional
from pydantic import BaseModel, ConfigDict

class ReferenceBase(BaseModel):
    publication_id: Optional[int] = None
    reference_text: Optional[str] = None
    doi: Optional[str] = None
    external_url: Optional[str] = None

class ReferenceCreate(ReferenceBase):
    publication_id: int
    reference_text: str

class ReferenceUpdate(ReferenceBase):
    pass

class ReferenceInDBBase(ReferenceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ReferenceOut(ReferenceInDBBase):
    pass
