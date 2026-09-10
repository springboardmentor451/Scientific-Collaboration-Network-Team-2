import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_validator, model_validator

from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    funding_source: str | None = None
    budget: Decimal | None = None
    status: ProjectStatus = ProjectStatus.PLANNED
    progress_percentage: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    lead_institution_id: uuid.UUID | None = None
    lead_researcher_id: uuid.UUID | None = None  # defaults to the submitter if omitted

    @field_validator("progress_percentage")
    @classmethod
    def progress_in_range(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("progress_percentage must be between 0 and 100")
        return v

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title cannot be blank")
        return v.strip()

    @field_validator("budget")
    @classmethod
    def budget_non_negative(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("budget cannot be negative")
        return v

    @model_validator(mode="after")
    def end_after_start(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    funding_source: str | None = None
    budget: Decimal | None = None
    status: ProjectStatus | None = None
    progress_percentage: int | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("progress_percentage")
    @classmethod
    def progress_in_range(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("progress_percentage must be between 0 and 100")
        return v

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title cannot be blank")
        return v.strip() if v else v

    @field_validator("budget")
    @classmethod
    def budget_non_negative(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("budget cannot be negative")
        return v

    @model_validator(mode="after")
    def end_after_start(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self
