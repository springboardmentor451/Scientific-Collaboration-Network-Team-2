from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Project, Publication, PublicationAuthor, Researcher, User, UserRole
from app.schemas.common import PublicationOut
from app.schemas.publication import ALLOWED_STATUS_TRANSITIONS, PublicationCreate, PublicationUpdate

router = APIRouter(prefix="/publications", tags=["publications-write"])

UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads" / "publications"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB


def _get_researcher_or_403(db: Session, current_user: User) -> Researcher:
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only accounts with a researcher profile can do this",
        )
    return researcher


@router.post("", response_model=PublicationOut, status_code=status.HTTP_201_CREATED)
def create_publication(
    payload: PublicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a publication. The logged-in researcher is automatically added as
    the corresponding (first) author; co_author_ids adds further co-authors.
    """
    researcher = _get_researcher_or_403(db, current_user)

    if payload.project_id and not db.get(Project, payload.project_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id does not exist")

    if payload.doi:
        existing = db.query(Publication).filter(Publication.doi == payload.doi).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A publication with this DOI already exists")

    co_authors = []
    for rid in payload.co_author_ids:
        r = db.get(Researcher, rid)
        if not r:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"co_author_ids contains unknown researcher {rid}")
        if r.id == researcher.id:
            continue  # avoid duplicating the submitter
        co_authors.append(r)

    publication = Publication(
        title=payload.title,
        abstract=payload.abstract,
        publication_type=payload.publication_type,
        doi=payload.doi,
        journal_or_venue=payload.journal_or_venue,
        volume=payload.volume,
        issue=payload.issue,
        pages=payload.pages,
        publication_date=payload.publication_date,
        project_id=payload.project_id,
    )
    db.add(publication)
    db.flush()

    db.add(PublicationAuthor(publication_id=publication.id, researcher_id=researcher.id, author_order=1, is_corresponding=True))
    for order, co in enumerate(co_authors, start=2):
        db.add(PublicationAuthor(publication_id=publication.id, researcher_id=co.id, author_order=order, is_corresponding=False))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create publication")

    db.refresh(publication)
    return publication


@router.put("/{publication_id}", response_model=PublicationOut)
def update_publication(
    publication_id: str,
    payload: PublicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates a publication. Only the corresponding author or a system admin
    may edit it. Status changes must follow the allowed workflow
    (draft -> submitted -> published -> archived).
    """
    publication = db.get(Publication, publication_id)
    if not publication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")

    if current_user.role != UserRole.SYSTEM_ADMIN:
        researcher = _get_researcher_or_403(db, current_user)
        is_corresponding_author = any(
            link.researcher_id == researcher.id and link.is_corresponding for link in publication.authors
        )
        if not is_corresponding_author:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the corresponding author or a system admin can edit this publication",
            )

    if payload.status is not None and payload.status != publication.status:
        allowed_next = ALLOWED_STATUS_TRANSITIONS.get(publication.status, set())
        if payload.status not in allowed_next:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot move status from '{publication.status.value}' to '{payload.status.value}'",
            )

    if payload.doi and payload.doi != publication.doi:
        clash = db.query(Publication).filter(Publication.doi == payload.doi).first()
        if clash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A publication with this DOI already exists")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(publication, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not update publication")

    db.refresh(publication)
    return publication


def _require_author_or_admin(db: Session, publication: Publication, current_user: User) -> None:
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return
    researcher = _get_researcher_or_403(db, current_user)
    is_author = any(link.researcher_id == researcher.id for link in publication.authors)
    if not is_author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an author of this publication or a system admin can do this",
        )


@router.post("/{publication_id}/file", response_model=PublicationOut)
def upload_publication_file(
    publication_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Attaches the actual paper (PDF/DOC/DOCX, up to 20MB) to a publication.
    Stored on local disk under backend/uploads/publications/ — swap for S3 in
    production by changing UPLOAD_ROOT + how the path is stored, the API
    shape here wouldn't need to change.
    """
    publication = db.get(Publication, publication_id)
    if not publication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")
    _require_author_or_admin(db, publication, current_user)

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type must be one of: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    contents = file.file.read()
    if len(contents) > MAX_FILE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is larger than the 20MB limit")

    dest_dir = UPLOAD_ROOT / str(publication.id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in (file.filename or "upload" + ext) if c.isalnum() or c in "._- ")[:150] or ("upload" + ext)
    dest_path = dest_dir / safe_name
    dest_path.write_bytes(contents)

    publication.file_path = str(dest_path.relative_to(UPLOAD_ROOT.parent.parent))
    db.commit()
    db.refresh(publication)
    return publication


@router.get("/{publication_id}/file")
def download_publication_file(publication_id: str, db: Session = Depends(get_db)):
    publication = db.get(Publication, publication_id)
    if not publication or not publication.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No file attached to this publication")
    full_path = UPLOAD_ROOT.parent.parent / publication.file_path
    if not full_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File is on record but missing on disk")
    return FileResponse(full_path, filename=publication.file_name)
