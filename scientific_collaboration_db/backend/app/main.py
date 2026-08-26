# """
# Minimal FastAPI layer sitting on top of the database models.

# This is intentionally small — its purpose is to prove the database layer
# works end-to-end (connection, models, relationships, queries), not to be
# the full application API. Extend the routers here as the rest of the
# platform (auth, write endpoints, dashboards, etc.) is built out.
# """
# from fastapi import Depends, FastAPI, HTTPException
# from sqlalchemy import text
# from sqlalchemy.orm import Session

# from app.database import get_db
# from app.models import Conference, Institution, Project, Publication, Researcher
# from app.routers import auth, projects, publications, researchers
# from app.schemas.common import ConferenceOut, InstitutionOut, ProjectOut, PublicationOut, ResearcherOut

# app = FastAPI(
#     title="Scientific Collaboration Network Analyzer - Database API",
#     description="API demonstrating the SQLAlchemy/PostgreSQL data layer, with authentication and validated write endpoints.",
#     version="0.2.0",
# )

# app.include_router(auth.router)
# app.include_router(researchers.router)
# app.include_router(publications.router)
# app.include_router(projects.router)


# @app.get("/health", tags=["system"])
# def health_check(db: Session = Depends(get_db)):
#     """Confirms the API process can reach PostgreSQL."""
#     db.execute(text("SELECT 1"))
#     return {"status": "ok", "database": "connected"}


# @app.get("/institutions", response_model=list[InstitutionOut], tags=["institutions"])
# def list_institutions(db: Session = Depends(get_db)):
#     return db.query(Institution).order_by(Institution.name).all()


# @app.get("/researchers", response_model=list[ResearcherOut], tags=["researchers"])
# def list_researchers(db: Session = Depends(get_db)):
#     return db.query(Researcher).order_by(Researcher.full_name).all()


# @app.get("/researchers/{researcher_id}", response_model=ResearcherOut, tags=["researchers"])
# def get_researcher(researcher_id: str, db: Session = Depends(get_db)):
#     researcher = db.get(Researcher, researcher_id)
#     if not researcher:
#         raise HTTPException(status_code=404, detail="Researcher not found")
#     return researcher


# @app.get("/publications", response_model=list[PublicationOut], tags=["publications"])
# def list_publications(db: Session = Depends(get_db)):
#     return db.query(Publication).order_by(Publication.publication_date.desc().nullslast()).all()


# @app.get("/projects", response_model=list[ProjectOut], tags=["projects"])
# def list_projects(db: Session = Depends(get_db)):
#     return db.query(Project).order_by(Project.start_date.desc().nullslast()).all()


# @app.get("/conferences", response_model=list[ConferenceOut], tags=["conferences"])
# def list_conferences(db: Session = Depends(get_db)):
#     return db.query(Conference).order_by(Conference.start_date.desc().nullslast()).all()


# @app.get("/researchers/{researcher_id}/collaboration-network", tags=["collaboration"])
# def researcher_collaboration_network(researcher_id: str, db: Session = Depends(get_db)):
#     """
#     Returns the co-author graph for a researcher: every distinct researcher
#     they have shared a publication with. This backs the network visualization
#     described in the project spec (without any AI-based analysis).
#     """
#     researcher = db.get(Researcher, researcher_id)
#     if not researcher:
#         raise HTTPException(status_code=404, detail="Researcher not found")

#     co_author_ids: set[str] = set()
#     shared_publications = []
#     for link in researcher.publication_links:
#         pub = link.publication
#         shared_publications.append({"publication_id": str(pub.id), "title": pub.title})
#         for other_link in pub.authors:
#             if str(other_link.researcher_id) != str(researcher_id):
#                 co_author_ids.add(str(other_link.researcher_id))

#     return {
#         "researcher_id": str(researcher_id),
#         "researcher_name": researcher.full_name,
#         "co_author_count": len(co_author_ids),
#         "co_author_ids": list(co_author_ids),
#         "publications": shared_publications,
#     }

"""
Minimal FastAPI layer sitting on top of the database models.

This is intentionally small — its purpose is to prove the database layer
works end-to-end (connection, models, relationships, queries), not to be
the full application API. Extend the routers here as the rest of the
platform (auth, write endpoints, dashboards, etc.) is built out.
"""
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conference, Institution, Project, Publication, PublicationAuthor, Researcher
from app.routers import (
    admin, auth, citations, conference_participations, conferences,
    institutions, projects, publications, researchers,
)
from app.schemas.common import ConferenceOut, InstitutionOut, ProjectOut, PublicationOut, ResearcherOut

app = FastAPI(
    title="Scientific Collaboration Network Analyzer - Database API",
    description="API demonstrating the SQLAlchemy/PostgreSQL data layer, with authentication and validated write endpoints.",
    version="0.4.0",
)

# Allows the standalone admin panel (opened as a local HTML file, a different
# origin from the API) to call this API directly from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Publicly serves uploaded avatar images directly (e.g. <img src="{API_BASE_URL}/uploads/avatars/...">).
# Publication files are intentionally NOT served this way — they go through
# the dedicated GET /publications/{id}/file endpoint instead, which sets a
# proper filename/content-disposition for downloading.
_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(_UPLOAD_DIR / "avatars").mkdir(parents=True, exist_ok=True)
app.mount("/uploads/avatars", StaticFiles(directory=str(_UPLOAD_DIR / "avatars")), name="avatars")

app.include_router(auth.router)
app.include_router(citations.router)
app.include_router(conference_participations.router)
app.include_router(researchers.router)
app.include_router(publications.router)
app.include_router(projects.router)
app.include_router(institutions.router)
app.include_router(conferences.router)
app.include_router(admin.router)


@app.get("/health", tags=["system"])
def health_check(db: Session = Depends(get_db)):
    """Confirms the API process can reach PostgreSQL."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/institutions", response_model=list[InstitutionOut], tags=["institutions"])
def list_institutions(db: Session = Depends(get_db)):
    return db.query(Institution).order_by(Institution.name).all()


@app.get("/researchers", response_model=list[ResearcherOut], tags=["researchers"])
def list_researchers(db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    return (
        db.query(Researcher)
        .options(joinedload(Researcher.institution), joinedload(Researcher.tags))
        .order_by(Researcher.full_name)
        .all()
    )


@app.get("/researchers/{researcher_id}", response_model=ResearcherOut, tags=["researchers"])
def get_researcher(researcher_id: str, db: Session = Depends(get_db)):
    researcher = db.get(Researcher, researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")
    return researcher


@app.get("/publications", response_model=list[PublicationOut], tags=["publications"])
def list_publications(db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    return (
        db.query(Publication)
        .options(joinedload(Publication.authors).joinedload(PublicationAuthor.researcher))
        .order_by(Publication.publication_date.desc().nullslast())
        .all()
    )


@app.get("/projects", response_model=list[ProjectOut], tags=["projects"])
def list_projects(db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    return (
        db.query(Project)
        .options(
            joinedload(Project.lead_institution),
            joinedload(Project.lead_researcher),
            joinedload(Project.members),
        )
        .order_by(Project.start_date.desc().nullslast())
        .all()
    )


@app.get("/conferences", response_model=list[ConferenceOut], tags=["conferences"])
def list_conferences(db: Session = Depends(get_db)):
    return db.query(Conference).order_by(Conference.start_date.desc().nullslast()).all()


@app.get("/researchers/{researcher_id}/collaboration-network", tags=["collaboration"])
def researcher_collaboration_network(researcher_id: str, db: Session = Depends(get_db)):
    """
    Returns the co-author graph for a researcher: every distinct researcher
    they have shared a publication with. This backs the network visualization
    described in the project spec (without any AI-based analysis).
    """
    researcher = db.get(Researcher, researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")

    co_author_ids: set[str] = set()
    shared_publications = []
    for link in researcher.publication_links:
        pub = link.publication
        shared_publications.append({"publication_id": str(pub.id), "title": pub.title})
        for other_link in pub.authors:
            if str(other_link.researcher_id) != str(researcher_id):
                co_author_ids.add(str(other_link.researcher_id))

    return {
        "researcher_id": str(researcher_id),
        "researcher_name": researcher.full_name,
        "co_author_count": len(co_author_ids),
        "co_author_ids": list(co_author_ids),
        "publications": shared_publications,
    }