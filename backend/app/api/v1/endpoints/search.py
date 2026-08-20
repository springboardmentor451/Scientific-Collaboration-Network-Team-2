from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.researchers import Researcher
from backend.app.models.publications import Publication
from backend.app.models.projects import Project
from backend.app.models.institutions import Institution
from backend.app.models.conferences import Conference

router = APIRouter()

@router.get("/search")
def global_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    db: Session = Depends(get_db),
    limit: int = 10
) -> Any:
    """
    Perform unified search across researchers, publications, projects, institutions, and conferences.
    """
    query_str = f"%{q}%"
    
    # 1. Researchers
    researchers_query = db.query(Researcher).filter(
        (Researcher.full_name.ilike(query_str)) |
        (Researcher.bio.ilike(query_str)) |
        (Researcher.affiliations.ilike(query_str))
    ).limit(limit).all()

    researchers_res = [
        {
            "id": r.id,
            "title": r.full_name,
            "subtitle": r.institution.name if r.institution else (r.affiliations or "Researcher"),
            "category": "Researchers",
            "url": f"/researchers?id={r.id}"
        }
        for r in researchers_query
    ]

    # 2. Publications
    pubs_query = db.query(Publication).filter(
        (Publication.title.ilike(query_str)) |
        (Publication.abstract.ilike(query_str)) |
        (Publication.venue.ilike(query_str)) |
        (Publication.doi.ilike(query_str))
    ).limit(limit).all()

    pubs_res = [
        {
            "id": p.id,
            "title": p.title,
            "subtitle": f"{p.type.value if hasattr(p.type, 'value') else p.type} • {p.venue or 'Academic Journal'}",
            "category": "Publications",
            "url": f"/publications?id={p.id}"
        }
        for p in pubs_query
    ]

    # 3. Projects
    projects_query = db.query(Project).filter(
        (Project.title.ilike(query_str)) |
        (Project.description.ilike(query_str)) |
        (Project.funding_source.ilike(query_str))
    ).limit(limit).all()

    projects_res = [
        {
            "id": pr.id,
            "title": pr.title,
            "subtitle": f"Funding: {pr.funding_source or 'N/A'}" + (f" • ${pr.funding_amount:,.2f}" if pr.funding_amount else ""),
            "category": "Projects",
            "url": f"/projects?id={pr.id}"
        }
        for pr in projects_query
    ]

    # 4. Institutions
    institutions_query = db.query(Institution).filter(
        (Institution.name.ilike(query_str)) |
        (Institution.address.ilike(query_str))
    ).limit(limit).all()

    institutions_res = [
        {
            "id": inst.id,
            "title": inst.name,
            "subtitle": f"{inst.type or 'Institution'}" + (f" • {inst.address}" if inst.address else ""),
            "category": "Institutions",
            "url": f"/dashboard"
        }
        for inst in institutions_query
    ]

    # 5. Conferences
    conferences_query = db.query(Conference).filter(
        (Conference.name.ilike(query_str)) |
        (Conference.location.ilike(query_str))
    ).limit(limit).all()

    conferences_res = [
        {
            "id": conf.id,
            "title": conf.name,
            "subtitle": f"{conf.location or ''} • {conf.start_date or ''}",
            "category": "Conferences",
            "url": f"/conferences?id={conf.id}"
        }
        for conf in conferences_query
    ]

    total_results = len(researchers_res) + len(pubs_res) + len(projects_res) + len(institutions_res) + len(conferences_res)

    return {
        "query": q,
        "total_results": total_results,
        "results": {
            "researchers": researchers_res,
            "publications": pubs_res,
            "projects": projects_res,
            "institutions": institutions_res,
            "conferences": conferences_res
        }
    }
