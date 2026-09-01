"""Role-safe grounding and local Ollama client for SCNA Assistant.

Only compact, already-authorized records are sent to the local model.  This
module intentionally has no access to passwords, JWTs, SMTP credentials, or
other application secrets.
"""
from __future__ import annotations

import json
import os
import threading
from collections import defaultdict
from urllib.error import URLError
from urllib.request import Request, urlopen

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.citation import Citation
from app.models.collaboration import CollaborationRequest
from app.models.conference import Conference
from app.models.institution import Institution
from app.models.project import Project
from app.models.publication import Publication
from app.models.researcher import Researcher
from app.models.review import Review
from app.models.user import User

MAX_RECORDS = 8
_locks: dict[int, threading.Lock] = defaultdict(threading.Lock)


def request_lock(user_id: int) -> threading.Lock:
    return _locks[user_id]


def immediate_help(message: str, user: User) -> str | None:
    """Answer non-data SCNA questions without inventing any database facts.

    This keeps a greeting useful even while a local model is warming up.
    """
    text = " ".join(message.casefold().split()).strip("!?. ")
    greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
    if text in greetings:
        return f"Hello, {user.full_name}. I’m SCNA Assistant. Ask me about your permitted publications, projects, collaborations, conferences, reports, or how to use SCNA."
    if text in {"help", "what can you do", "what can you do for me", "how can you help"}:
        return "I can explain SCNA modules and summarize the records your role is allowed to access. Try asking about publications, projects, collaborations, conferences, reviews, or reports."
    if "how do reports work" in text or "how does report work" in text:
        return "Use Reports & Analytics to view your role-safe publication and collaboration information. System Admins can generate institution reports; Institution Admins can generate reports only for their assigned institution."
    return None


def _topic(message: str) -> str:
    value = message.casefold()
    if any(word in value for word in ("publication", "paper", "doi", "author", "journal")):
        return "publications"
    if any(word in value for word in ("project", "milestone", "team")):
        return "projects"
    if any(word in value for word in ("collaboration", "collaborator", "co-author")):
        return "collaborations"
    if any(word in value for word in ("review", "reviewer")):
        return "reviews"
    if any(word in value for word in ("conference", "event", "participation")):
        return "conferences"
    if any(word in value for word in ("citation", "reference")):
        return "citations"
    if any(word in value for word in ("institution", "university", "department")):
        return "institutions"
    if any(word in value for word in ("researcher", "research interest", "skill")):
        return "researchers"
    if any(word in value for word in ("report", "analytic", "statistics", "count")):
        return "reports"
    return "overview"


def _publication(item: Publication) -> dict:
    return {"title": item.title, "authors": item.authors, "year": item.publication_year, "status": item.status, "venue": item.venue, "doi_or_url": item.doi_url}


def _project(item: Project) -> dict:
    return {"title": item.title, "status": item.status, "research_area": item.research_area, "start_date": str(item.start_date) if item.start_date else None, "end_date": str(item.end_date) if item.end_date else None}


def _collaboration(item: CollaborationRequest) -> dict:
    return {"requester": item.requester_name, "recipient": item.recipient_name, "status": item.status, "created_at": item.created_at.isoformat()}


def _own_context(db: Session, user: User, topic: str) -> dict:
    context = {"scope": "only the current user's records", "user": {"name": user.full_name, "role": user.role}}
    if topic in {"publications", "overview", "reports"}:
        context["publications"] = [_publication(item) for item in db.query(Publication).filter(Publication.owner_id == user.id).order_by(Publication.publication_year.desc()).limit(MAX_RECORDS).all()]
    if topic in {"projects", "overview"}:
        context["projects"] = [_project(item) for item in db.query(Project).filter(or_(Project.owner_id == user.id, Project.researchers.any(Researcher.user_id == user.id))).order_by(Project.title).limit(MAX_RECORDS).all()]
    if topic in {"collaborations", "overview", "reports"}:
        context["collaborations"] = [_collaboration(item) for item in db.query(CollaborationRequest).filter(or_(CollaborationRequest.requester_id == user.id, CollaborationRequest.recipient_id == user.id)).order_by(CollaborationRequest.created_at.desc()).limit(MAX_RECORDS).all()]
    if topic in {"conferences", "overview"}:
        context["conferences"] = [{"title": item.title, "starts_at": item.starts_at.isoformat(), "location": item.location} for item in db.query(Conference).filter(Conference.participants.any(User.id == user.id)).order_by(Conference.starts_at.desc()).limit(MAX_RECORDS).all()]
    if topic == "citations":
        context["citations"] = [{"title": item.cited_title, "authors": item.cited_authors, "url": item.cited_url} for item in db.query(Citation).filter(Citation.owner_id == user.id).order_by(Citation.created_at.desc()).limit(MAX_RECORDS).all()]
    return context


def _institution_context(db: Session, user: User, topic: str) -> dict:
    if not user.institution_id:
        return {"scope": "no institution is assigned to this account", "records": []}
    institution = db.query(Institution).filter(Institution.id == user.institution_id).first()
    context = {"scope": "only the assigned institution", "institution": institution.name if institution else user.institution}
    user_ids = db.query(User.id).filter(User.institution_id == user.institution_id)
    if topic in {"researchers", "overview", "reports"}:
        context["researchers"] = [{"name": item.name, "department": item.department, "field": item.field} for item in db.query(Researcher).filter(Researcher.institution_id == user.institution_id).order_by(Researcher.name).limit(MAX_RECORDS).all()]
    if topic in {"publications", "overview", "reports"}:
        context["publications"] = [_publication(item) for item in db.query(Publication).filter(Publication.owner_id.in_(user_ids)).order_by(Publication.publication_year.desc()).limit(MAX_RECORDS).all()]
    if topic in {"projects", "overview", "reports"}:
        context["projects"] = [_project(item) for item in db.query(Project).filter(Project.owner_id.in_(user_ids)).order_by(Project.title).limit(MAX_RECORDS).all()]
    if topic in {"collaborations", "overview", "reports"}:
        context["collaborations"] = [_collaboration(item) for item in db.query(CollaborationRequest).filter(or_(CollaborationRequest.requester_id.in_(user_ids), CollaborationRequest.recipient_id.in_(user_ids))).order_by(CollaborationRequest.created_at.desc()).limit(MAX_RECORDS).all()]
    return context


def _admin_context(db: Session, topic: str) -> dict:
    counts = {"users": db.query(User).count(), "researchers": db.query(Researcher).count(), "institutions": db.query(Institution).count(), "publications": db.query(Publication).count(), "projects": db.query(Project).count(), "collaborations": db.query(CollaborationRequest).count(), "reviews": db.query(Review).count()}
    context = {"scope": "system-wide administrative records", "counts": counts}
    if topic == "researchers": context["researchers"] = [{"name": item.name, "institution": item.institution, "field": item.field} for item in db.query(Researcher).order_by(Researcher.name).limit(MAX_RECORDS).all()]
    if topic == "institutions": context["institutions"] = [{"name": item.name, "location": item.location} for item in db.query(Institution).order_by(Institution.name).limit(MAX_RECORDS).all()]
    if topic == "publications": context["publications"] = [_publication(item) for item in db.query(Publication).order_by(Publication.publication_year.desc()).limit(MAX_RECORDS).all()]
    if topic == "projects": context["projects"] = [_project(item) for item in db.query(Project).order_by(Project.title).limit(MAX_RECORDS).all()]
    if topic == "collaborations": context["collaborations"] = [_collaboration(item) for item in db.query(CollaborationRequest).order_by(CollaborationRequest.created_at.desc()).limit(MAX_RECORDS).all()]
    if topic == "reviews": context["reviews"] = [{"publication": item.publication.title, "reviewer": item.reviewer.full_name, "status": item.status} for item in db.query(Review).order_by(Review.created_at.desc()).limit(MAX_RECORDS).all()]
    return context


def _reviewer_context(db: Session, user: User) -> dict:
    return {"scope": "only reviews assigned to the current reviewer", "reviews": [{"publication": item.publication.title, "status": item.status, "comments": item.comments, "assigned_at": item.created_at.isoformat()} for item in db.query(Review).filter(Review.reviewer_id == user.id).order_by(Review.created_at.desc()).limit(MAX_RECORDS).all()]}


def build_context(db: Session, user: User, message: str) -> tuple[dict, str, str | None]:
    topic = _topic(message)
    links = {"publications": "/publications", "projects": "/projects", "collaborations": "/collaborations", "reviews": "/reviews", "conferences": "/conferences", "citations": "/citations", "institutions": "/institutions", "researchers": "/researchers", "reports": "/reports"}
    if user.role in {"Admin", "System Admin"}:
        context = _admin_context(db, topic)
    elif user.role == "Institution Admin":
        context = _institution_context(db, user, topic)
    elif user.role == "Reviewer":
        context = _reviewer_context(db, user)
    else:
        context = _own_context(db, user, topic)
    return context, topic, links.get(topic)


def record_answer(context: dict, topic: str, message: str) -> str | None:
    """Return exact small lists/counts directly from already-authorized context.

    This is more accurate and faster than asking a compact local model to
    count records. Open-ended summaries continue to use Ollama.
    """
    question = message.casefold()
    direct_request = any(phrase in question for phrase in ("how many", "count", "statistics", "statistic", "list", "show", "which", "summarize", "summary"))
    if not direct_request:
        return None
    counts = context.get("counts")
    if counts and topic in {"reports", "overview"}:
        return "Current SCNA totals: " + ", ".join(f"{name.replace('_', ' ')}: {value}" for name, value in counts.items()) + "."
    records = context.get(topic)
    if not isinstance(records, list):
        return None
    if not records:
        return f"There are no {topic} in your available SCNA records."
    if topic == "publications":
        titles = [f"{item['title']} ({item.get('status', 'Unknown')}, {item.get('year', 'Unknown')})" for item in records]
        return "Available publications: " + "; ".join(titles) + "."
    if topic == "projects":
        return "Available projects: " + "; ".join(f"{item['title']} ({item.get('status', 'Unknown')})" for item in records) + "."
    if topic == "reviews":
        return "Available reviews: " + "; ".join(f"{item.get('publication', 'Publication')} ({item.get('status', 'Unknown')})" for item in records) + "."
    return f"{topic.title()} in your available SCNA records: {len(records)}."


def ask_ollama(message: str, context: dict) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
    prompt = (
        "You are SCNA Assistant for a scientific collaboration platform. You may respond naturally and briefly to greetings, thanks, and general SCNA feature questions. "
        "For every question about data, answer only from the supplied SCNA records. Never invent names, counts, dates, publications, projects, permissions, or records. If the records do not contain the requested data, say: "
        "'I could not find that information in your available SCNA records.' Keep the answer concise, clear, and under 120 words.\n\n"
        f"SCNA records (authorized scope only):\n{json.dumps(context, ensure_ascii=False, default=str)}\n\nUser question: {message}"
    )
    # Keep model work bounded so the UI never waits for an unreasonably long
    # generation. Exact lists and counts already use the direct database path.
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1, "num_predict": 48}}).encode()
    request = Request(f"{base_url}/api/generate", data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "8"))) as response:
            payload = json.loads(response.read().decode())
    except (URLError, TimeoutError, OSError, ValueError) as error:
        raise RuntimeError("The assistant is temporarily unavailable. Please try again.") from error
    answer = str(payload.get("response", "")).strip()
    if not answer:
        return "I could not find that information in your available SCNA records."
    return answer[:1800]
