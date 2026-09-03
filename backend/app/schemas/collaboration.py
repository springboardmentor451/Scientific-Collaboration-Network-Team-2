from datetime import date, datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


class CollaborationBase(BaseModel):

    researcher_id_1: int

    researcher_id_2: int

    institution_1_name: Optional[str] = Field(default=None, max_length=200)

    institution_2_name: Optional[str] = Field(default=None, max_length=200)

    collaboration_type: Optional[str] = Field(
        default="Co-authorship",
        max_length=100
    )

    description: Optional[str] = None

    start_date: Optional[date] = None

    end_date: Optional[date] = None

    status: Optional[str] = Field(
        default="Pending",
        max_length=50
    )


class CollaborationCreate(
    CollaborationBase
):
    pass


class CollaborationUpdate(BaseModel):

    researcher_id_1: Optional[int] = None

    researcher_id_2: Optional[int] = None

    collaboration_type: Optional[str] = Field(
        default=None,
        max_length=100
    )

    description: Optional[str] = None

    start_date: Optional[date] = None

    end_date: Optional[date] = None

    status: Optional[str] = Field(
        default=None,
        max_length=50
    )


class CollaborationResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    researcher_id_1: int

    researcher_id_2: int

    researcher_1_name: Optional[str] = None

    researcher_2_name: Optional[str] = None

    institution_1: Optional[str] = None

    institution_2: Optional[str] = None

    collaboration_type: Optional[str] = None

    description: Optional[str] = None

    start_date: Optional[date] = None

    end_date: Optional[date] = None

    status: Optional[str] = None

    created_at: Optional[datetime] = None


class CollaborationStatsResponse(BaseModel):

    total_collaborations: int

    active: int

    completed: int

    pending: int

    cancelled: int