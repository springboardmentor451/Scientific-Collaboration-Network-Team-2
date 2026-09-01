from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.publication import Publication
from app.models.collaboration import CollaborationRequest
from app.models.conference import Conference
from app.models.project import Project
from app.models.researcher import Researcher
from app.models.review import Review
from datetime import datetime,timezone

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/me")
def my_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == "Reviewer":
        reviews = db.query(Review).filter(Review.reviewer_id == user.id)
        return {
            "publications": reviews.with_entities(Review.publication_id).distinct().count(),
            "projects": 0,
            "collaborations": 0,
            "pending_requests": 0,
            "research_interests": user.research_interests or [],
            "upcoming_conferences": 0,
            "pending_reviews": reviews.filter(Review.status == "Pending").count(),
            "completed_reviews": reviews.filter(Review.status.in_(["Approved", "Rejected"])).count(),
        }
    if user.role == "Institution Admin":
        institution_users = db.query(User).filter(User.institution_id == user.institution_id)
        institution_publications = db.query(Publication).join(User, Publication.owner_id == User.id).filter(User.institution_id == user.institution_id)
        institution_projects = db.query(Project).join(User, Project.owner_id == User.id).filter(User.institution_id == user.institution_id)
        institution_user_ids = institution_users.with_entities(User.id)
        return {
            "publications": institution_publications.count(),
            "projects": institution_projects.count(),
            "collaborations": db.query(CollaborationRequest).filter(or_(CollaborationRequest.requester_id.in_(institution_user_ids), CollaborationRequest.recipient_id.in_(institution_user_ids)), CollaborationRequest.status == "Accepted").count(),
            "pending_requests": db.query(CollaborationRequest).filter(CollaborationRequest.recipient_id.in_(institution_user_ids), CollaborationRequest.status == "Pending").count(),
            "research_interests": user.research_interests or [],
            "upcoming_conferences": db.query(Conference).filter(Conference.starts_at >= datetime.now(timezone.utc)).count(),
            "institution_researchers": db.query(Researcher).filter(Researcher.institution_id == user.institution_id).count(),
            "draft_publications": institution_publications.filter(Publication.status == "Draft").count(),
            "submitted_publications": institution_publications.filter(Publication.status == "Submitted").count(),
            "published_publications": institution_publications.filter(Publication.status == "Published").count(),
            "archived_publications": institution_publications.filter(Publication.status == "Archived").count(),
        }
    publications = db.query(Publication).filter(Publication.owner_id == user.id).count()
    publication_statuses = {
        status: db.query(Publication).filter(
            Publication.owner_id == user.id,
            Publication.status == status,
        ).count()
        for status in ("Draft", "Submitted", "Published", "Archived")
    }
    projects = db.query(Project).filter(or_(Project.owner_id == user.id, Project.researchers.any(Researcher.user_id == user.id))).count()
    collaborations = db.query(CollaborationRequest).filter(or_(CollaborationRequest.requester_id == user.id, CollaborationRequest.recipient_id == user.id), CollaborationRequest.status == "Accepted").count()
    pending = db.query(CollaborationRequest).filter(CollaborationRequest.recipient_id == user.id, CollaborationRequest.status == "Pending").count()
    upcoming=db.query(Conference).filter(Conference.starts_at>=datetime.now(timezone.utc)).count()
    return {
        "publications": publications,
        "projects": projects,
        "collaborations": collaborations,
        "pending_requests": pending,
        "research_interests": user.research_interests or [],
        "upcoming_conferences": upcoming,
        "draft_publications": publication_statuses["Draft"],
        "submitted_publications": publication_statuses["Submitted"],
        "published_publications": publication_statuses["Published"],
        "archived_publications": publication_statuses["Archived"],
    }
