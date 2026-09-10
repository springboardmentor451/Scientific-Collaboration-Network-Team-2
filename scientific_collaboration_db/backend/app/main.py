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

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conference, Institution, Project, Publication, PublicationAuthor, Researcher, User, UserRole
from app.routers import (
    admin, auth, citations, conference_participations, conferences,
    institutions, projects, publications, researchers, reviews,
)
from app.schemas.common import ConferenceOut, InstitutionOut, ProjectOut, PublicationOut, ResearcherOut

app = FastAPI(
    title="Scientific Collaboration Network Analyzer - Database API",
    description="API demonstrating the SQLAlchemy/PostgreSQL data layer, with authentication and validated write endpoints.",
    version="0.4.0",
)


@app.on_event("startup")
def _warn_on_default_secret_key():
    """
    Every checkout of this project ships the same placeholder SECRET_KEY in
    .env.example so it works out of the box for local development — but
    that also means it's public (it's sitting in source control) and must
    never be used once real user data or a public deployment is involved,
    since it's what signs every access token and password-reset link. This
    fails loudly rather than silently accepting it in anything other than
    an explicit development environment.
    """
    from app.core.config import get_settings as _get_settings
    s = _get_settings()
    if s.SECRET_KEY == "change-this-secret-key-in-production":
        if s.APP_ENV.lower() == "development":
            print(
                "\n  WARNING: SECRET_KEY is the default placeholder value. This is fine for local "
                "development, but generate a real one (e.g. `python -c \"import secrets; "
                "print(secrets.token_urlsafe(48))\"`) and set it in .env before deploying anywhere "
                "real users or real data can reach this server.\n"
            )
        else:
            raise RuntimeError(
                "SECRET_KEY is still the default placeholder value and APP_ENV is not "
                "'development'. Refusing to start: generate a real SECRET_KEY (e.g. "
                "`python -c \"import secrets; print(secrets.token_urlsafe(48))\"`) and set it "
                "in .env before running outside local development."
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
app.include_router(reviews.router)


@app.get("/health", tags=["system"])
def health_check(db: Session = Depends(get_db)):
    """Confirms the API process can reach PostgreSQL."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/institutions", response_model=list[InstitutionOut], tags=["institutions"])
def list_institutions(
    db: Session = Depends(get_db),
    limit: int | None = Query(None, ge=1, le=500, description="Max rows to return. Omit for the full list (current behavior)."),
    offset: int = Query(0, ge=0),
):
    query = db.query(Institution).order_by(Institution.name).offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


@app.get("/researchers", response_model=list[ResearcherOut], tags=["researchers"])
def list_researchers(
    db: Session = Depends(get_db),
    limit: int | None = Query(None, ge=1, le=500, description="Max rows to return. Omit for the full list (current behavior)."),
    offset: int = Query(0, ge=0),
):
    from sqlalchemy.orm import joinedload
    query = (
        db.query(Researcher)
        .join(User, User.id == Researcher.user_id)
        # A promoted Researcher (now Reviewer/Institution Admin) keeps their
        # Researcher row forever, on purpose — it's the authorship record
        # behind their past publications and project memberships. But it
        # shouldn't keep showing up in the "browse our researchers" list
        # once that's no longer their actual role; that list is for people
        # to reach out to as researchers today, not a full account history.
        .filter(User.role == UserRole.RESEARCHER)
        .options(joinedload(Researcher.institution), joinedload(Researcher.tags))
        .order_by(Researcher.full_name)
        .offset(offset)
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


@app.get("/researchers/{researcher_id}", response_model=ResearcherOut, tags=["researchers"])
def get_researcher(researcher_id: str, db: Session = Depends(get_db)):
    researcher = db.get(Researcher, researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")
    return researcher


@app.get("/publications", response_model=list[PublicationOut], tags=["publications"])
def list_publications(
    db: Session = Depends(get_db),
    limit: int | None = Query(None, ge=1, le=500, description="Max rows to return. Omit for the full list (current behavior)."),
    offset: int = Query(0, ge=0),
):
    from sqlalchemy.orm import joinedload
    query = (
        db.query(Publication)
        .options(joinedload(Publication.authors).joinedload(PublicationAuthor.researcher).joinedload(Researcher.institution))
        .order_by(Publication.publication_date.desc().nullslast())
        .offset(offset)
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


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