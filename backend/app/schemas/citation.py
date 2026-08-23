from typing import Optional

from pydantic import BaseModel, model_validator


class CitationBase(BaseModel):
    citing_publication_id: int
    cited_publication_id: Optional[int] = None
    external_reference: Optional[str] = None
    doi: Optional[str] = None

    @model_validator(mode="after")
    def check_target(self):
        if not self.cited_publication_id and not self.external_reference:
            raise ValueError(
                "Either cited_publication_id (internal) or external_reference "
                "(external work) must be provided"
            )
        return self


class CitationCreate(CitationBase):
    pass


class CitationUpdate(BaseModel):
    external_reference: Optional[str] = None
    doi: Optional[str] = None


class CitationOut(CitationBase):
    id: int

    class Config:
        from_attributes = True


class CitationReport(BaseModel):
    publication_id: int
    citation_count: int
    cited_by: list[CitationOut]
