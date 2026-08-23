from typing import Optional

from pydantic import BaseModel


class CountByCategory(BaseModel):
    category: str
    count: int


class PublicationReport(BaseModel):
    total_publications: int
    by_status: list[CountByCategory]
    by_type: list[CountByCategory]
    by_year: list[CountByCategory]


class InstitutionReportRow(BaseModel):
    institution_id: int
    institution_name: str
    researcher_count: int
    publication_count: int


class InstitutionReport(BaseModel):
    institutions: list[InstitutionReportRow]


class CollaborationReport(BaseModel):
    total_researchers_in_network: int
    total_collaboration_links: int
    total_shared_publications: int
    total_shared_projects: int


class ResearcherDashboard(BaseModel):
    researcher_id: int
    name: str
    publication_count: int
    project_count: int
    conference_participation_count: int
    collaborator_count: int


class InstitutionDashboard(BaseModel):
    institution_id: int
    institution_name: str
    departments: list[str]
    researcher_count: int
    publication_count: int
    active_project_count: int


class AdminDashboard(BaseModel):
    total_researchers: int
    total_institutions: int
    total_publications: int
    total_projects: int
    total_conferences: int
    total_users: int
    publication_report: PublicationReport
