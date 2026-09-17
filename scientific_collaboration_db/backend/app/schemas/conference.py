import uuid
from datetime import date

from pydantic import BaseModel, field_validator, model_validator


class ConferenceCreate(BaseModel):
    name: str
    location: str | None = None
    website: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    # Optional on the wire — a System Admin may pick any institution (or
    # leave it unset for a platform-wide conference); an Institution Admin's
    # value here is ignored server-side in favor of their own institution.
    institution_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be blank")
        return v.strip()

    @model_validator(mode="after")
    def end_after_start(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class ConferenceUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    website: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    institution_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name cannot be blank")
        return v.strip() if v else v

    @model_validator(mode="after")
    def end_after_start(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self