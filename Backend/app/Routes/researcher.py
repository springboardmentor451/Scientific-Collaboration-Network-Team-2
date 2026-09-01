from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.Crud import researcher as researcher_crud
from app.Schemas.researcher import ResearcherCreate, ResearcherResponse, ResearcherUpdate
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.publication import Publication
from app.models.collaboration import CollaborationRequest
from app.Crud.audit import log_action
from app.models.institution import Institution
from sqlalchemy import func


router = APIRouter(prefix="/researchers", tags=["Researchers"])


def researcher_response(db: Session, researcher):
    data = {field: getattr(researcher, field) for field in ("id", "user_id", "institution_id", "name", "email", "department", "institution", "field", "skills", "research_interests", "affiliation", "source", "source_url")}
    if not researcher.user_id:
        data["email"] = None
    if researcher.user_id:
        data["publication_count"] = db.query(Publication).filter(Publication.owner_id == researcher.user_id).count()
        data["collaboration_count"] = db.query(CollaborationRequest).filter(
            or_(CollaborationRequest.requester_id == researcher.user_id, CollaborationRequest.recipient_id == researcher.user_id),
            CollaborationRequest.status == "Accepted",
        ).count()
    else:
        data["publication_count"] = 0
        data["collaboration_count"] = 0
    return data


@router.post("", response_model=ResearcherResponse, status_code=status.HTTP_201_CREATED)
def create_researcher(researcher: ResearcherCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in {"Researcher", "Faculty", "Institution Admin", "Admin", "System Admin"}:
        raise HTTPException(status_code=403, detail="Your role cannot create a researcher profile.")
    existing_profile = db.query(researcher_crud.Researcher).filter(researcher_crud.Researcher.user_id == current_user.id).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="You already have a researcher profile.")
    if researcher_crud.get_researcher_by_email(db, researcher.email):
        raise HTTPException(status_code=400, detail="Researcher email already registered.")
    institution = db.query(Institution).filter(func.lower(Institution.name) == researcher.institution.lower()).first()
    created = researcher_crud.create_researcher(db, researcher, current_user.id, institution.id if institution else None)
    log_action(db, "RESEARCHER_CREATED", current_user.id, "Researcher", created.id, created.name); db.commit()
    return researcher_response(db, created)


@router.get("", response_model=list[ResearcherResponse])
def list_researchers(
    search: str | None = Query(default=None, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "Institution Admin":
        if not current_user.institution_id:
            raise HTTPException(403, "Your account is not assigned to an institution.")
        query = db.query(researcher_crud.Researcher).filter(
            researcher_crud.Researcher.institution_id == current_user.institution_id
        )
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(or_(
                researcher_crud.Researcher.name.ilike(pattern),
                researcher_crud.Researcher.email.ilike(pattern),
                researcher_crud.Researcher.department.ilike(pattern),
                researcher_crud.Researcher.field.ilike(pattern),
            ))
        items = query.order_by(researcher_crud.Researcher.name).offset(skip).limit(limit).all()
    else:
        items = researcher_crud.get_researchers(db, search=search, skip=skip, limit=limit)
    return [researcher_response(db, item) for item in items]


@router.get("/{researcher_id}", response_model=ResearcherResponse)
def get_researcher(researcher_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    researcher = researcher_crud.get_researcher(db, researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found.")
    if current_user.role == "Institution Admin" and researcher.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="You can only view researchers from your institution.")
    return researcher_response(db, researcher)


@router.put("/{researcher_id}", response_model=ResearcherResponse)
def update_researcher(
    researcher_id: int,
    researcher_update: ResearcherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    researcher = researcher_crud.get_researcher(db, researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found.")

    is_institution_manager = current_user.role == "Institution Admin" and researcher.institution_id == current_user.institution_id
    if researcher.user_id != current_user.id and current_user.role not in {"Admin", "System Admin"} and not is_institution_manager:
        raise HTTPException(status_code=403, detail="You can only update your own researcher profile.")

    if current_user.role == "Institution Admin" and researcher_update.institution:
        assigned_institution = db.query(Institution).filter(Institution.id == current_user.institution_id).first()
        if not assigned_institution or researcher_update.institution.lower() != assigned_institution.name.lower():
            raise HTTPException(status_code=403, detail="You can only assign your own institution.")

    if researcher_update.email:
        email_owner = researcher_crud.get_researcher_by_email(db, researcher_update.email)
        if email_owner and email_owner.id != researcher_id:
            raise HTTPException(status_code=400, detail="Researcher email already registered.")

    if researcher_update.institution:
        institution = db.query(Institution).filter(func.lower(Institution.name) == researcher_update.institution.lower()).first()
        researcher.institution_id = institution.id if institution else None

    updated = researcher_crud.update_researcher(db, researcher, researcher_update)
    log_action(db, "RESEARCHER_UPDATED", current_user.id, "Researcher", updated.id, updated.name)
    db.commit()
    return researcher_response(db, updated)


@router.delete("/{researcher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_researcher(researcher_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    researcher = researcher_crud.get_researcher(db, researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found.")
    is_institution_manager = current_user.role == "Institution Admin" and researcher.institution_id == current_user.institution_id
    if researcher.user_id != current_user.id and current_user.role not in {"Admin", "System Admin"} and not is_institution_manager:
        raise HTTPException(status_code=403, detail="You can only delete your own researcher profile.")
    log_action(db, "RESEARCHER_DELETED", current_user.id, "Researcher", researcher.id, researcher.name)
    researcher_crud.delete_researcher(db, researcher)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
