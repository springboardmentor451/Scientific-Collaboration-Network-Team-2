from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.conference import ConferenceParticipation
from app.models.institution import Institution
from app.models.project import ProjectStatus, ResearchProject, project_members
from app.models.publication import Publication, publication_authors
from app.models.researcher import Researcher
from app.models.user import User
from app.schemas.report import CountByCategory
from app.services import collaboration as collaboration_service


def publication_report(db: Session) -> dict:
    total = db.query(Publication).count()

    by_status = (
        db.query(Publication.status, func.count(Publication.id))
        .group_by(Publication.status)
        .all()
    )
    by_type = (
        db.query(Publication.publication_type, func.count(Publication.id))
        .group_by(Publication.publication_type)
        .all()
    )
    by_year = (
        db.query(Publication.year, func.count(Publication.id))
        .filter(Publication.year.isnot(None))
        .group_by(Publication.year)
        .all()
    )

    return {
        "total_publications": total,
        "by_status": [
            CountByCategory(category=s.value if s else "unknown", count=c)
            for s, c in by_status
        ],
        "by_type": [
            CountByCategory(category=t.value if t else "unknown", count=c)
            for t, c in by_type
        ],
        "by_year": [
            CountByCategory(category=str(y), count=c) for y, c in by_year
        ],
    }


def institution_report(db: Session) -> dict:
    institutions = db.query(Institution).all()
    rows = []
    for inst in institutions:
        researcher_count = (
            db.query(Researcher).filter(Researcher.institution_id == inst.id).count()
        )
        publication_count = (
            db.query(Publication)
            .join(publication_authors)
            .join(Researcher, Researcher.id == publication_authors.c.researcher_id)
            .filter(Researcher.institution_id == inst.id)
            .distinct()
            .count()
        )
        rows.append(
            {
                "institution_id": inst.id,
                "institution_name": inst.name,
                "researcher_count": researcher_count,
                "publication_count": publication_count,
            }
        )
    return {"institutions": rows}


def collaboration_report(db: Session) -> dict:
    network = collaboration_service.build_collaboration_network(db)
    return {
        "total_researchers_in_network": len(network.nodes),
        "total_collaboration_links": len(network.edges),
        "total_shared_publications": sum(e.shared_publications for e in network.edges),
        "total_shared_projects": sum(e.shared_projects for e in network.edges),
    }


def researcher_dashboard(db: Session, researcher_id: int) -> dict:
    researcher = db.query(Researcher).filter(Researcher.id == researcher_id).first()
    if not researcher:
        raise ValueError("Researcher not found")

    publication_count = (
        db.query(Publication)
        .join(publication_authors)
        .filter(publication_authors.c.researcher_id == researcher_id)
        .count()
    )
    project_count = (
        db.query(ResearchProject)
        .join(project_members)
        .filter(project_members.c.researcher_id == researcher_id)
        .count()
    )
    conference_count = (
        db.query(ConferenceParticipation)
        .filter(ConferenceParticipation.researcher_id == researcher_id)
        .count()
    )
    collaborator_count = len(
        collaboration_service.get_researcher_collaborators(db, researcher_id)
    )

    return {
        "researcher_id": researcher.id,
        "name": researcher.name,
        "publication_count": publication_count,
        "project_count": project_count,
        "conference_participation_count": conference_count,
        "collaborator_count": collaborator_count,
    }


def institution_dashboard(db: Session, institution_id: int) -> dict:
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise ValueError("Institution not found")

    researchers = (
        db.query(Researcher).filter(Researcher.institution_id == institution_id).all()
    )
    researcher_ids = [r.id for r in researchers]
    departments = sorted({r.department for r in researchers if r.department})

    publication_count = 0
    if researcher_ids:
        publication_count = (
            db.query(Publication)
            .join(publication_authors)
            .filter(publication_authors.c.researcher_id.in_(researcher_ids))
            .distinct()
            .count()
        )

    active_project_count = (
        db.query(ResearchProject)
        .filter(
            ResearchProject.institutions.any(Institution.id == institution_id),
            ResearchProject.status == ProjectStatus.ACTIVE,
        )
        .count()
    )

    return {
        "institution_id": institution.id,
        "institution_name": institution.name,
        "departments": departments,
        "researcher_count": len(researchers),
        "publication_count": publication_count,
        "active_project_count": active_project_count,
    }


def admin_dashboard(db: Session) -> dict:
    return {
        "total_researchers": db.query(Researcher).count(),
        "total_institutions": db.query(Institution).count(),
        "total_publications": db.query(Publication).count(),
        "total_projects": db.query(ResearchProject).count(),
        "total_conferences": db.query(ConferenceParticipation.conference_id.distinct()).count(),
        "total_users": db.query(User).count(),
        "publication_report": publication_report(db),
    }
