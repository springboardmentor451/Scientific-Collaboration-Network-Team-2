from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.audit import log_action
from app.core.deps import get_current_user, require_roles
from app.core.email import send_review_assigned_email, send_review_decided_email
from app.database import get_db
from app.models import (
    Publication, PublicationAuthor, PublicationReview, PublicationStatus,
    Researcher, ReviewStatus, User, UserRole,
)
from app.schemas.review import ReviewAssignCreate, ReviewDecisionUpdate, ReviewerOut, ReviewOut

router = APIRouter(prefix="/reviews", tags=["reviews"])

admin_or_institution_admin = require_roles("system_admin", "institution_admin")
reviewer_only = require_roles("reviewer")


def _is_system_admin(user: User) -> bool:
    return user.role == UserRole.SYSTEM_ADMIN


def _publication_institution_id(publication: Publication) -> UUID | None:
    """
    The institution a publication 'belongs to' — the corresponding author's
    institution, falling back to the first author's, so Institution Admins
    can be scoped to reviews on their own institution's work.
    """
    corresponding = next((a for a in publication.authors if a.is_corresponding), None)
    link = corresponding or (publication.authors[0] if publication.authors else None)
    if link and link.researcher:
        return link.researcher.institution_id
    return None


def _review_out(review: PublicationReview) -> dict:
    reviewer_name = None
    if review.reviewer:
        reviewer_name = review.reviewer.researcher.full_name if review.reviewer.researcher else review.reviewer.email.split("@")[0]
    return {
        "id": review.id,
        "publication_id": review.publication_id,
        "publication_title": review.publication.title if review.publication else None,
        "publication_status": review.publication.status.value if review.publication else None,
        "reviewer_id": review.reviewer_id,
        "reviewer_name": reviewer_name,
        "reviewer_email": review.reviewer.email if review.reviewer else None,
        "assigned_by_id": review.assigned_by_id,
        "assigned_by_email": review.assigned_by.email if review.assigned_by else None,
        "status": review.status.value,
        "note": review.note,
        "comments": review.comments,
        "assigned_at": review.assigned_at,
        "decided_at": review.decided_at,
    }


def _review_query(db: Session):
    return db.query(PublicationReview).options(
        joinedload(PublicationReview.publication).joinedload(Publication.authors).joinedload(PublicationAuthor.researcher),
        joinedload(PublicationReview.reviewer).joinedload(User.researcher),
        joinedload(PublicationReview.assigned_by),
    )


# ============================================================
# REVIEWER DIRECTORY (for the "assign a reviewer" dropdown)
# ============================================================
@router.get("/reviewers", response_model=list[ReviewerOut])
def list_reviewers(db: Session = Depends(get_db), current_user: User = Depends(admin_or_institution_admin)):
    """
    System Admin sees every reviewer on the platform. Institution Admin only
    sees reviewers scoped to their own institution — so they can only hand
    work to people who actually belong to it.
    """
    query = db.query(User).options(
        joinedload(User.researcher), joinedload(User.institution)
    ).filter(User.role == UserRole.REVIEWER, User.is_active == True)  # noqa: E712
    reviewers = query.order_by(User.email).all()

    if not _is_system_admin(current_user):
        admin_inst = current_user.effective_institution_id
        if not admin_inst:
            return []
        # Filtered in Python (not SQL) because a reviewer's institution can
        # come from either User.institution_id or a Researcher profile.
        reviewers = [r for r in reviewers if r.effective_institution_id == admin_inst]
    return [
        {
            "id": r.id,
            "email": r.email,
            "full_name": r.researcher.full_name if r.researcher else None,
            "institution_id": r.effective_institution_id,
            "institution_name": r.institution.name if r.institution else (r.researcher.institution.name if r.researcher and r.researcher.institution else None),
            "is_active": r.is_active,
        }
        for r in reviewers
    ]


# ============================================================
# ASSIGN / LIST / CANCEL (system_admin, institution_admin)
# ============================================================
@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def assign_reviewer(
    payload: ReviewAssignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_institution_admin),
):
    publication = (
        db.query(Publication)
        .options(joinedload(Publication.authors).joinedload(PublicationAuthor.researcher))
        .filter(Publication.id == payload.publication_id)
        .first()
    )
    if not publication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")

    reviewer = db.get(User, payload.reviewer_id)
    if not reviewer or reviewer.role != UserRole.REVIEWER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="reviewer_id must belong to an active Reviewer account")
    if not reviewer.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That reviewer account is currently blocked")

    if not _is_system_admin(current_user):
        admin_inst = current_user.effective_institution_id
        if not admin_inst:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account isn't linked to an institution yet")
        if _publication_institution_id(publication) != admin_inst:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only assign reviewers to publications from your own institution")
        if reviewer.effective_institution_id != admin_inst:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only assign reviewers who belong to your own institution")

    existing = (
        db.query(PublicationReview)
        .filter(
            PublicationReview.publication_id == publication.id,
            PublicationReview.reviewer_id == reviewer.id,
            PublicationReview.status == ReviewStatus.PENDING,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This reviewer already has a pending review on this publication")

    review = PublicationReview(
        publication_id=publication.id,
        reviewer_id=reviewer.id,
        assigned_by_id=current_user.id,
        status=ReviewStatus.PENDING,
        note=payload.note,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    if reviewer.email_notifications_enabled:
        send_review_assigned_email(reviewer.email, publication.title, payload.note)

    log_action(db, current_user.id, "ASSIGN", "PublicationReview", review.id, {
        "publication_id": str(publication.id), "reviewer_email": reviewer.email,
    })

    review = _review_query(db).filter(PublicationReview.id == review.id).first()
    return _review_out(review)


@router.get("", response_model=list[ReviewOut])
def list_reviews(
    review_status: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_institution_admin),
):
    query = _review_query(db)
    if review_status:
        try:
            query = query.filter(PublicationReview.status == ReviewStatus(review_status))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown status '{review_status}'")

    reviews = query.order_by(PublicationReview.assigned_at.desc()).all()

    if not _is_system_admin(current_user):
        admin_inst = current_user.effective_institution_id
        reviews = [r for r in reviews if admin_inst and _publication_institution_id(r.publication) == admin_inst]

    return [_review_out(r) for r in reviews]


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_review(review_id: str, db: Session = Depends(get_db), current_user: User = Depends(admin_or_institution_admin)):
    review = (
        db.query(PublicationReview)
        .options(joinedload(PublicationReview.publication).joinedload(Publication.authors).joinedload(PublicationAuthor.researcher))
        .filter(PublicationReview.id == review_id)
        .first()
    )
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review assignment not found")
    if review.status != ReviewStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a pending (undecided) review assignment can be cancelled")

    if not _is_system_admin(current_user):
        admin_inst = current_user.effective_institution_id
        if not admin_inst or _publication_institution_id(review.publication) != admin_inst:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only cancel reviews on your own institution's publications")

    log_action(db, current_user.id, "CANCEL", "PublicationReview", review.id, {"publication_id": str(review.publication_id)})
    db.delete(review)
    db.commit()


# ============================================================
# REVIEWER'S OWN QUEUE
# ============================================================
@router.get("/mine", response_model=list[ReviewOut])
def my_reviews(db: Session = Depends(get_db), current_user: User = Depends(reviewer_only)):
    reviews = _review_query(db).filter(PublicationReview.reviewer_id == current_user.id).order_by(
        PublicationReview.assigned_at.desc()
    ).all()
    return [_review_out(r) for r in reviews]


@router.post("/{review_id}/decision", response_model=ReviewOut)
def submit_review_decision(
    review_id: str,
    payload: ReviewDecisionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(reviewer_only),
):
    review = (
        db.query(PublicationReview)
        .options(joinedload(PublicationReview.publication))
        .filter(PublicationReview.id == review_id)
        .first()
    )
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review assignment not found")
    if str(review.reviewer_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This review isn't assigned to you")
    if review.status != ReviewStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This review has already been decided")

    review.status = ReviewStatus(payload.status)
    review.comments = payload.comments
    review.decided_at = datetime.now(timezone.utc)

    # A reviewer's decision has real teeth: it moves the publication along
    # the workflow instead of just being a label nobody acts on.
    publication = review.publication
    if publication and publication.status == PublicationStatus.SUBMITTED:
        if review.status == ReviewStatus.APPROVED:
            publication.status = PublicationStatus.PUBLISHED
        elif review.status == ReviewStatus.REJECTED:
            publication.status = PublicationStatus.DRAFT

    db.commit()
    db.refresh(review)

    log_action(db, current_user.id, "REVIEW_DECISION", "PublicationReview", review.id, {
        "status": review.status.value, "publication_id": str(review.publication_id),
    })

    if publication:
        author_link = next((a for a in publication.authors if a.is_corresponding), None) or (
            publication.authors[0] if publication.authors else None
        )
        author_user = None
        if author_link and author_link.researcher:
            author_user = db.get(User, author_link.researcher.user_id)
        if author_user and author_user.email_notifications_enabled:
            send_review_decided_email(author_user.email, publication.title, review.status.value, review.comments)

    review = _review_query(db).filter(PublicationReview.id == review.id).first()
    return _review_out(review)
