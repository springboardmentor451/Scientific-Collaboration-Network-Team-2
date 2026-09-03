from datetime import date
from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from .database.connection import engine, ensure_captcha_schema, test_connection
from .database.base import Base

from .routes.auth import router as auth_router
from .routes.researcher import router as researcher_router, get_researcher_data
from .routes.publications import router as publication_router

from backend.app.models.conferences import Conference
from backend.app.models.conference_participants import ConferenceParticipant
from backend.app.models.collaborations import Collaboration
from backend.app.models.publication_authors import PublicationAuthor
from backend.app.models.captcha_challenges import CaptchaChallenge

from backend.app.routes.conference import router as conferences_router
from backend.app.routes.collaboration import router as collaborations_router
from backend.app.auth.oauth2 import get_current_user
from backend.app.database.session import get_db

from sqlalchemy import func
from sqlalchemy.orm import Session

# =========================================================
# IMPORT MODELS
# =========================================================

from .models.users import *
from .models.researchers import Researcher
from .models.institutions import Institution
from .models.publications import Publication


from backend.app.routes.profile import router as profile_router
from backend.app.routes.admin import router as admin_router
from backend.app.routes.settings import router as settings_router

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Scientific Collaboration Network Analyzer"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(
    bind=engine
)
ensure_captcha_schema()


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message":
        "Scientific Collaboration Network Analyzer"
    }


@app.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    pending_collaborations = db.query(Collaboration).filter(
        Collaboration.status.ilike("pending")
    ).count()
    upcoming_conferences = [
        conference for conference in db.query(Conference).all()
        if conference.start_date and conference.start_date >= date.today()
    ]

    items = []
    if pending_collaborations:
        items.append({
            "type": "collaboration",
            "message": f"{pending_collaborations} pending collaboration(s)"
        })
    if upcoming_conferences:
        items.append({
            "type": "conference",
            "message": f"{len(upcoming_conferences)} upcoming conference(s)"
        })

    return {
        "unread_count": len(items),
        "items": items
    }


# =========================================================
# DATABASE TEST
# =========================================================

@app.get("/db-test")
def db_test():

    if test_connection():

        return {
            "status": "success",
            "message":
            "Database connected successfully!"
        }

    return {
        "status": "failed",
        "message":
        "Database connection failed!"
    }


# =========================================================
# DASHBOARD SUMMARY
# =========================================================

@app.get("/dashboard/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    total_researchers = db.query(Researcher).count()
    total_institutions = db.query(Institution).count()
    total_publications = db.query(Publication).count()
    total_conferences = db.query(Conference).count()
    total_collaborations = db.query(Collaboration).count()

    field_counts = {}
    for researcher in db.query(Researcher).all():
        field_name = (researcher.research_area or "General Research").strip()
        if not field_name:
            field_name = "General Research"
        field_counts[field_name] = field_counts.get(field_name, 0) + 1

    research_fields = []
    if field_counts:
        max_fields = max(field_counts.values())
        for name, count in sorted(field_counts.items(), key=lambda item: (-item[1], item[0]))[:5]:
            research_fields.append({
                "name": name,
                "count": count,
                "percent": round((count / max_fields) * 100) if max_fields else 0
            })

    country_counts = (
        db.query(Institution.country, func.count(Researcher.id).label("researcher_count"))
        .outerjoin(Researcher, Researcher.institution_id == Institution.id)
        .filter(Institution.country.isnot(None))
        .group_by(Institution.country)
        .order_by(func.count(Researcher.id).desc())
        .limit(6)
        .all()
    )

    top_countries = []
    if country_counts:
        max_country_count = max(count for _, count in country_counts)
        for country, count in country_counts:
            top_countries.append({
                "name": country,
                "count": count,
                "percent": round((count / max_country_count) * 100) if max_country_count else 0
            })

    publication_rows = db.query(Publication.publication_date).all()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_counts = {month: 0 for month in month_names}

    for publication_date, in publication_rows:
        if publication_date is None:
            continue
        month_index = publication_date.month - 1
        if 0 <= month_index < 12:
            month_counts[month_names[month_index]] += 1

    publication_trend = [
        {"month": month, "value": month_counts[month]}
        for month in month_names
    ]

    weekly_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekly_counts = {label: 0 for label in weekly_labels}

    collaborations = db.query(Collaboration).all()
    for collaboration in collaborations:
        if collaboration.created_at is None:
            continue
        weekday_name = collaboration.created_at.strftime("%a")
        if weekday_name in weekly_counts:
            weekly_counts[weekday_name] += 1

    weekly_activity = [
        {"day": label, "value": weekly_counts.get(label, 0)}
        for label in weekly_labels
    ]

    def get_user_name(researcher_id):
        researcher = db.query(Researcher).filter(Researcher.id == researcher_id).first()
        if not researcher:
            return "Unknown Researcher"
        user = db.query(User).filter(User.id == researcher.user_id).first()
        return user.full_name if user and user.full_name else "Unknown Researcher"

    recent_collaborations = []
    for collaboration in db.query(Collaboration).order_by(Collaboration.created_at.desc()).limit(5).all():
        recent_collaborations.append({
            "id": collaboration.id,
            "researcher_1": get_user_name(collaboration.researcher_id_1),
            "researcher_2": get_user_name(collaboration.researcher_id_2),
            "collaboration_type": collaboration.collaboration_type or "Co-authorship",
            "status": collaboration.status or "Active",
        })

    all_researchers = []
    for researcher in db.query(Researcher).all():
        metrics = get_researcher_data(researcher, db)
        all_researchers.append(metrics)

    all_researchers.sort(
        key=lambda item: (
            item.get("h_index", 0),
            item.get("papers", 0),
            item.get("citations", 0)
        ),
        reverse=True
    )

    top_researchers = []
    for index, researcher in enumerate(all_researchers[:5], start=1):
        top_researchers.append({
            "rank": index,
            "name": researcher.get("full_name") or "Unknown Researcher",
            "institution": researcher.get("institution_name") or "Unknown Institution",
            "field": researcher.get("research_area") or "General Research",
            "h_index": researcher.get("h_index", 0),
            "papers": researcher.get("papers", 0),
            "citations": researcher.get("citations", 0),
            "status": researcher.get("status") or "Active",
        })

    return {
        "stats": [
            {"label": "Total Researchers", "value": total_researchers, "trend": "+{} this month".format(total_researchers // 20 if total_researchers else 0)},
            {"label": "Institutions", "value": total_institutions, "trend": "+{} this month".format(total_institutions // 10 if total_institutions else 0)},
            {"label": "Publications", "value": total_publications, "trend": "+{} this month".format(total_publications // 50 if total_publications else 0)},
            {"label": "Conferences", "value": total_conferences, "trend": "+{} this month".format(total_conferences // 10 if total_conferences else 0)},
            {"label": "Collaborations", "value": total_collaborations, "trend": "+{} this month".format(total_collaborations // 30 if total_collaborations else 0)},
        ],
        "research_fields": research_fields,
        "top_countries": top_countries,
        "publication_trend": publication_trend,
        "weekly_activity": weekly_activity,
        "recent_collaborations": recent_collaborations,
        "top_researchers": top_researchers,
    }


# =========================================================
# ROUTERS
# =========================================================

app.include_router(auth_router)

app.include_router(researcher_router)

app.include_router(publication_router)

app.include_router(conferences_router)

app.include_router(collaborations_router)

app.include_router(profile_router)
app.include_router(admin_router)
app.include_router(settings_router)