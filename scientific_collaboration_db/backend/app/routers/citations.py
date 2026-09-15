from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.deps import get_current_user
from app.core.email import send_email
from app.database import get_db
from app.models import Citation, Publication, Researcher, User, UserRole
from app.schemas.citation import CitationCreate, CitationUpdate
from app.schemas.common import CitationOut

router = APIRouter(prefix="/citations", tags=["citations"])


def _get_researcher_or_403(db: Session, current_user: User) -> Researcher:
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only accounts with a researcher profile can do this",
        )
    return researcher


def _assert_can_edit_publication(db: Session, current_user: User, publication: Publication):
    """Only the corresponding author of `publication` or a system admin may add/edit its citations."""
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return
    researcher = _get_researcher_or_403(db, current_user)
    is_corresponding_author = any(
        link.researcher_id == researcher.id and link.is_corresponding for link in publication.authors
    )
    if not is_corresponding_author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the corresponding author of the citing publication (or a system admin) can do this",
        )


@router.get("", response_model=list[CitationOut])
def list_citations(
    citing_publication_id: str | None = None,
    cited_publication_id: str | None = None,
    db: Session = Depends(get_db),
):
    """List citations, optionally filtered by the citing or cited publication."""
    query = db.query(Citation)
    if citing_publication_id:
        query = query.filter(Citation.citing_publication_id == citing_publication_id)
    if cited_publication_id:
        query = query.filter(Citation.cited_publication_id == cited_publication_id)
    return query.order_by(Citation.created_at.desc()).all()


@router.get("/{citation_id}", response_model=CitationOut)
def get_citation(citation_id: str, db: Session = Depends(get_db)):
    citation = db.get(Citation, citation_id)
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    return citation


@router.post("", response_model=CitationOut, status_code=status.HTTP_201_CREATED)
def create_citation(
    payload: CitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    citing_pub = db.get(Publication, payload.citing_publication_id)
    if not citing_pub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="citing_publication_id does not exist")
    _assert_can_edit_publication(db, current_user, citing_pub)

    if payload.cited_publication_id:
        cited_pub = db.get(Publication, payload.cited_publication_id)
        if not cited_pub:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cited_publication_id does not exist")
        if str(cited_pub.id) == str(citing_pub.id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A publication cannot cite itself")

    citation = Citation(**payload.model_dump())
    db.add(citation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create citation")
    db.refresh(citation)
    log_action(db, current_user.id, "CREATE", "Citation", citation.id, {"citing_publication_id": str(citing_pub.id)})

    # Real notification: email every author of the cited publication (if
    # they have email_notifications_enabled), gated by their actual saved
    # preference — this is what that Settings toggle was built to control.
    if payload.cited_publication_id:
        cited_pub = db.get(Publication, payload.cited_publication_id)
        if cited_pub:
            for link in cited_pub.authors:
                author_user = link.researcher.user if link.researcher else None
                if author_user and author_user.email_notifications_enabled and author_user.id != current_user.id:
                    send_email(
                        author_user.email,
                        "Your publication was cited — Scientific Collaboration Network Analyzer",
                        (
                            f"Hi,\n\nYour publication \"{cited_pub.title}\" was just cited by "
                            f"\"{citing_pub.title}\".\n\n"
                            f"You can turn these emails off anytime from Settings.\n"
                        ),
                    )

    return citation


@router.put("/{citation_id}", response_model=CitationOut)
def update_citation(
    citation_id: str,
    payload: CitationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    citation = db.get(Citation, citation_id)
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    _assert_can_edit_publication(db, current_user, citation.citing_publication)

    changed = payload.model_dump(exclude_unset=True)
    for field, value in changed.items():
        setattr(citation, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not update citation")
    db.refresh(citation)
    log_action(db, current_user.id, "UPDATE", "Citation", citation.id, {"fields": list(changed.keys())})
    return citation


@router.delete("/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_citation(
    citation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    citation = db.get(Citation, citation_id)
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    _assert_can_edit_publication(db, current_user, citation.citing_publication)

    db.delete(citation)
    db.commit()
    log_action(db, current_user.id, "DELETE", "Citation", citation_id, {})