from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Institution, Project, ProjectMember, Researcher, User, UserRole
from app.schemas.common import ProjectOut
from app.schemas.project import ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects-write"])


def _get_researcher_or_403(db: Session, current_user: User) -> Researcher:
    researcher = db.query(Researcher).filter(Researcher.user_id == current_user.id).first()
    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only accounts with a researcher profile can do this",
        )
    return researcher


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a project. Defaults lead_researcher_id to the submitter if not given."""
    researcher = _get_researcher_or_403(db, current_user)

    lead_researcher_id = payload.lead_researcher_id or researcher.id
    if payload.lead_researcher_id and not db.get(Researcher, payload.lead_researcher_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="lead_researcher_id does not exist")
    if payload.lead_institution_id and not db.get(Institution, payload.lead_institution_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="lead_institution_id does not exist")

    project = Project(
        title=payload.title,
        description=payload.description,
        funding_source=payload.funding_source,
        budget=payload.budget,
        status=payload.status,
        progress_percentage=payload.progress_percentage,
        start_date=payload.start_date,
        end_date=payload.end_date,
        lead_institution_id=payload.lead_institution_id,
        lead_researcher_id=lead_researcher_id,
    )
    db.add(project)
    db.flush()

    db.add(ProjectMember(project_id=project.id, researcher_id=lead_researcher_id, role="Principal Investigator"))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create project")

    db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Only the project's lead researcher, an institution admin, or a system admin may edit it."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role not in (UserRole.SYSTEM_ADMIN, UserRole.INSTITUTION_ADMIN):
        researcher = _get_researcher_or_403(db, current_user)
        if project.lead_researcher_id != researcher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the lead researcher, an institution admin, or a system admin can edit this project",
            )

    update_data = payload.model_dump(exclude_unset=True)

    new_start = update_data.get("start_date", project.start_date)
    new_end = update_data.get("end_date", project.end_date)
    if new_start and new_end and new_end < new_start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_date cannot be before start_date")

    for field, value in update_data.items():
        setattr(project, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not update project")

    db.refresh(project)
    return project
