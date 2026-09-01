from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.Crud.audit import log_action
from app.models.publication import Publication
from app.models.review import Review
from app.models.user import User
from app.Schemas.review import ReviewAssign, ReviewDecision, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/assign", response_model=ReviewResponse, status_code=201)
def assign_review(data: ReviewAssign, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    publication = db.query(Publication).filter(Publication.id == data.publication_id).first()
    reviewer = db.query(User).filter(User.id == data.reviewer_id, User.role == "Reviewer", User.is_active.is_(True), User.approval_status == "Approved").first()
    if not publication: raise HTTPException(404, "Publication not found.")
    if not reviewer: raise HTTPException(400, "Select an active approved Reviewer account.")
    if db.query(Review).filter(Review.publication_id == publication.id, Review.reviewer_id == reviewer.id, Review.status == "Pending").first(): raise HTTPException(400, "This reviewer already has a pending review for this publication.")
    item = Review(publication_id=publication.id, reviewer_id=reviewer.id, assigned_by_id=admin.id)
    db.add(item); db.flush(); log_action(db, "REVIEW_ASSIGNED", admin.id, "Review", item.id, publication.title); db.commit(); db.refresh(item)
    return item

@router.get("/my-queue", response_model=list[ReviewResponse])
def my_queue(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "Reviewer": raise HTTPException(403, "Reviewer access required.")
    return db.query(Review).filter(Review.reviewer_id == user.id).order_by(Review.created_at.desc()).all()

@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Review).filter(Review.id == review_id).first()
    if not item: raise HTTPException(404, "Review not found.")
    if item.reviewer_id != user.id and user.role not in {"Admin", "System Admin"}:
        raise HTTPException(403, "You can only view your assigned reviews.")
    return item

@router.get("", response_model=list[ReviewResponse])
def all_reviews(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return db.query(Review).order_by(Review.created_at.desc()).all()

@router.post("/{review_id}/decision", response_model=ReviewResponse)
def decide_review(review_id: int, data: ReviewDecision, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Review).filter(Review.id == review_id).first()
    if not item: raise HTTPException(404, "Review not found.")
    if item.reviewer_id != user.id: raise HTTPException(403, "Only the assigned reviewer can decide this review.")
    if item.status != "Pending": raise HTTPException(400, "This review has already been decided.")
    item.status = data.status; item.comments = data.comments; item.decided_at = datetime.now(timezone.utc)
    log_action(db, "REVIEW_DECIDED", user.id, "Review", item.id, data.status); db.commit(); db.refresh(item)
    return item
