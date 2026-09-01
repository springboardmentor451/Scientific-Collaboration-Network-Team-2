from pydantic import BaseModel, ConfigDict, Field

class PublicationCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    authors: str = Field(min_length=2, max_length=500)
    abstract: str | None = Field(default=None, max_length=5000)
    research_area: str = Field(min_length=2, max_length=200)
    venue: str = Field(min_length=2, max_length=250)
    publication_year: int = Field(ge=1900, le=2100)
    doi_url: str | None = Field(default=None, max_length=500)
    publication_type: str = Field(default="Journal Article", max_length=80)
    status: str = Field(default="Draft", max_length=20)

class PublicationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=300)
    authors: str | None = Field(default=None, min_length=2, max_length=500)
    abstract: str | None = Field(default=None, max_length=5000)
    research_area: str | None = Field(default=None, min_length=2, max_length=200)
    venue: str | None = Field(default=None, min_length=2, max_length=250)
    publication_year: int | None = Field(default=None, ge=1900, le=2100)
    doi_url: str | None = Field(default=None, max_length=500)
    publication_type: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, max_length=20)

class PublicationResponse(PublicationCreate):
    id: int
    owner_id: int
    owner_name: str
    document_path: str | None = None
    researcher_author_ids: list[int] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
