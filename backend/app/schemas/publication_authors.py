from typing import Optional
from pydantic import BaseModel, ConfigDict

class PublicationAuthorBase(BaseModel):
    publication_id: Optional[int] = None
    researcher_id: Optional[int] = None
    author_order: Optional[int] = 1
    is_corresponding_author: Optional[bool] = False

class PublicationAuthorCreate(PublicationAuthorBase):
    publication_id: int
    researcher_id: int

class PublicationAuthorUpdate(BaseModel):
    author_order: Optional[int] = None
    is_corresponding_author: Optional[bool] = None

class PublicationAuthorInDBBase(PublicationAuthorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class PublicationAuthorOut(PublicationAuthorInDBBase):
    pass
