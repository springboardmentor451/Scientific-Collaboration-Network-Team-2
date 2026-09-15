import re
import uuid

from pydantic import BaseModel, field_validator, model_validator

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")


class CitationCreate(BaseModel):
    citing_publication_id: uuid.UUID
    cited_publication_id: uuid.UUID | None = None
    external_title: str | None = None
    external_doi: str | None = None
    external_authors: str | None = None

    @field_validator("external_doi")
    @classmethod
    def doi_format(cls, v: str | None) -> str | None:
        if v is not None and not DOI_PATTERN.match(v):
            raise ValueError("external_doi must look like 10.xxxx/suffix")
        return v

    @model_validator(mode="after")
    def has_a_target(self):
        if not self.cited_publication_id and not self.external_title:
            raise ValueError(
                "Provide either cited_publication_id (citing another publication in the system) "
                "or external_title (citing a work outside the system)"
            )
        if self.cited_publication_id and self.external_title:
            raise ValueError("Provide only one of cited_publication_id or external_title, not both")
        return self


class CitationUpdate(BaseModel):
    external_title: str | None = None
    external_doi: str | None = None
    external_authors: str | None = None

    @field_validator("external_doi")
    @classmethod
    def doi_format(cls, v: str | None) -> str | None:
        if v is not None and not DOI_PATTERN.match(v):
            raise ValueError("external_doi must look like 10.xxxx/suffix")
        return v