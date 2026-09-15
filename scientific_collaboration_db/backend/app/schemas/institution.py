from pydantic import BaseModel, field_validator


class InstitutionCreate(BaseModel):
    name: str
    country: str | None = None
    address: str | None = None
    website: str | None = None
    institution_type: str | None = None

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be blank")
        return v.strip()


class InstitutionUpdate(BaseModel):
    name: str | None = None
    country: str | None = None
    address: str | None = None
    website: str | None = None
    institution_type: str | None = None

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name cannot be blank")
        return v.strip() if v else v