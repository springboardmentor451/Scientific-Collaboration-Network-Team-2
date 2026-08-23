from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.models.project import ProjectStatus
from app.schemas.institution import InstitutionOut
from app.schemas.researcher import ResearcherOut


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNED
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    funding_agency: Optional[str] = None
    funding_amount: Optional[float] = None


class ProjectCreate(ProjectBase):
    institution_ids: list[int] = []


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    funding_agency: Optional[str] = None
    funding_amount: Optional[float] = None
    institution_ids: Optional[list[int]] = None


class ProjectOut(ProjectBase):
    id: int
    members: list[ResearcherOut] = []
    institutions: list[InstitutionOut] = []

    class Config:
        from_attributes = True


class ProjectMemberAdd(BaseModel):
    researcher_id: int
    role_in_project: Optional[str] = None


class CollaborationEdge(BaseModel):
    researcher_a_id: int
    researcher_a_name: str
    researcher_b_id: int
    researcher_b_name: str
    shared_publications: int
    shared_projects: int


class CollaborationNetwork(BaseModel):
    nodes: list[ResearcherOut]
    edges: list[CollaborationEdge]
