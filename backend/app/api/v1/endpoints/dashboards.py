from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.users import User, UserRole
from backend.app.models.researchers import Researcher
from backend.app.models.publications import Publication, PublicationStatus
from backend.app.models.publication_authors import PublicationAuthor
from backend.app.models.projects import Project, ProjectStatus
from backend.app.models.project_assignments import ProjectAssignment
from backend.app.models.conferences import Conference
from backend.app.models.conference_participation import ConferenceParticipation
from backend.app.models.collaborations import Collaboration, CollaborationType
from backend.app.models.institutions import Institution
from backend.app.models.departments import Department
from backend.app.api.deps import get_current_active_user, RoleChecker

router = APIRouter()

@router.get("/dashboards/researcher/{id}")
def get_researcher_dashboard(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get profile stats and list records for researcher dashboard.
    """
    researcher = db.query(Researcher).filter(Researcher.id == id).first()
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher profile not found")
        
    # Security check: only own or admin
    if current_user.id != researcher.user_id and current_user.role != UserRole.system_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dashboard profile")

    # 1. Publications
    # We query the publication table joining via secondary table
    publications = db.query(Publication).join(PublicationAuthor).filter(PublicationAuthor.researcher_id == id).all()

    # 2. Projects
    projects = db.query(Project).join(ProjectAssignment).filter(ProjectAssignment.researcher_id == id).all()

    # 3. Conferences
    conferences = db.query(Conference).join(ConferenceParticipation).filter(ConferenceParticipation.researcher_id == id).all()

    # Co-authors
    shared_pubs = db.query(PublicationAuthor.publication_id).filter(PublicationAuthor.researcher_id == id).subquery()
    co_author_ids_query = db.query(PublicationAuthor.researcher_id).filter(
        PublicationAuthor.publication_id.in_(shared_pubs),
        PublicationAuthor.researcher_id != id
    ).subquery()
    co_authors = db.query(Researcher).filter(Researcher.id.in_(co_author_ids_query)).all()

    return {
        "researcher": {
            "id": researcher.id,
            "full_name": researcher.full_name,
            "orcid_id": researcher.orcid_id,
            "interests": researcher.research_interests or [],
            "skills": researcher.skills or [],
            "bio": researcher.bio
        },
        "publications": [
            {"id": p.id, "title": p.title, "venue": p.venue, "date": str(p.publication_date), "status": p.status.value, "type": p.type.value}
            for p in publications
        ],
        "projects": [
            {"id": pr.id, "title": pr.title, "status": pr.status.value, "funding": float(pr.funding_amount or 0)}
            for pr in projects
        ],
        "conferences": [
            {"id": c.id, "name": c.name, "location": c.location, "start_date": str(c.start_date)}
            for c in conferences
        ],
        "collaborators": [
            {"id": ca.id, "full_name": ca.full_name, "institution": ca.institution.name if ca.institution else "None"}
            for ca in co_authors
        ]
    }


@router.get("/dashboards/institution/{id}")
def get_institution_dashboard(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get profile stats and list records for institution dashboard.
    """
    inst = db.query(Institution).filter(Institution.id == id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # 1. Departments
    depts = db.query(Department).filter(Department.institution_id == id).all()

    # 2. Researchers count
    researchers_count = db.query(Researcher).filter(Researcher.institution_id == id).count()

    # 3. Publications from researchers inside this institution
    inst_researchers = db.query(Researcher.id).filter(Researcher.institution_id == id).subquery()
    pub_ids_query = db.query(PublicationAuthor.publication_id).filter(
        PublicationAuthor.researcher_id.in_(inst_researchers)
    ).subquery()
    publications = db.query(Publication).filter(Publication.id.in_(pub_ids_query)).all()

    # 4. Active projects
    projects = db.query(Project).filter(
        Project.institution_id == id,
        Project.status == ProjectStatus.active
    ).all()

    # 5. Collaborations count
    internal_collab = db.query(Collaboration).filter(
        Collaboration.institution_id_1 == id,
        Collaboration.institution_id_2 == id
    ).count()
    
    external_collab = db.query(Collaboration).filter(
        ((Collaboration.institution_id_1 == id) & (Collaboration.institution_id_2 != id)) |
        ((Collaboration.institution_id_1 != id) & (Collaboration.institution_id_2 == id))
    ).count()

    return {
        "institution": {
            "id": inst.id,
            "name": inst.name,
            "type": inst.type,
            "website": inst.website
        },
        "departments": [{"id": d.id, "name": d.name} for d in depts],
        "researchers_count": researchers_count,
        "publications": [
            {"id": p.id, "title": p.title, "venue": p.venue, "date": str(p.publication_date)}
            for p in publications
        ],
        "active_projects": [
            {"id": pr.id, "title": pr.title, "funding": float(pr.funding_amount or 0)}
            for pr in projects
        ],
        "collaboration_stats": {
            "internal_count": internal_collab,
            "external_count": external_collab
        }
    }


@router.get("/dashboards/admin")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.system_admin, UserRole.institution_admin]))
) -> Dict[str, Any]:
    """
    Get aggregated counts and analytics for admin dashboard.
    """
    total_researchers = db.query(Researcher).count()
    total_publications = db.query(Publication).count()
    total_projects = db.query(Project).count()
    total_collaborations = db.query(Collaboration).count()

    # User statistics grouped by role
    user_stats_query = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    user_stats = {role.value: count for role, count in user_stats_query}

    # Institution analytics
    inst_analytics = []
    institutions = db.query(Institution).all()
    for inst in institutions:
        res_count = db.query(Researcher).filter(Researcher.institution_id == inst.id).count()
        inst_researchers = db.query(Researcher.id).filter(Researcher.institution_id == inst.id).subquery()
        pub_count = db.query(Publication).join(PublicationAuthor).filter(
            PublicationAuthor.researcher_id.in_(inst_researchers)
        ).distinct().count()
        
        inst_analytics.append({
            "id": inst.id,
            "name": inst.name,
            "researchers_count": res_count,
            "publications_count": pub_count
        })

    return {
        "system_stats": {
            "total_researchers": total_researchers,
            "total_publications": total_publications,
            "total_projects": total_projects,
            "total_collaborations": total_collaborations
        },
        "user_statistics": user_stats,
        "institution_analytics": inst_analytics
    }
