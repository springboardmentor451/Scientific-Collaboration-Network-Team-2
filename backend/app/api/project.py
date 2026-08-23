from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.project import ProjectStatus
from app.schemas.project import (
    CollaborationEdge,
    CollaborationNetwork,
    ProjectCreate,
    ProjectMemberAdd,
    ProjectOut,
    ProjectUpdate,
)
from app.services import collaboration as collaboration_service
from app.services import project as project_service

router = APIRouter(prefix="/projects", tags=["Collaboration & Projects"])


@router.post("/", response_model=ProjectOut)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    try:
        return project_service.create_new_project(db, project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}", response_model=ProjectOut)
def read_project(project_id: int, db: Session = Depends(get_db)):
    try:
        return project_service.get_project_by_id(db, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=list[ProjectOut])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    status: ProjectStatus | None = None,
    db: Session = Depends(get_db),
):
    return project_service.list_projects(db, skip, limit, status)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, project: ProjectUpdate, db: Session = Depends(get_db)):
    try:
        return project_service.update_existing_project(db, project_id, project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    try:
        project_service.delete_existing_project(db, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/members", response_model=ProjectOut)
def add_member(project_id: int, member: ProjectMemberAdd, db: Session = Depends(get_db)):
    try:
        return project_service.add_project_member(
            db, project_id, member.researcher_id, member.role_in_project
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/members/{researcher_id}", response_model=ProjectOut)
def remove_member(project_id: int, researcher_id: int, db: Session = Depends(get_db)):
    try:
        return project_service.remove_project_member(db, project_id, researcher_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


collaboration_router = APIRouter(prefix="/collaborations", tags=["Collaboration & Projects"])


@collaboration_router.get("/network", response_model=CollaborationNetwork)
def read_collaboration_network(db: Session = Depends(get_db)):
    return collaboration_service.build_collaboration_network(db)


@collaboration_router.get(
    "/researcher/{researcher_id}", response_model=list[CollaborationEdge]
)
def read_researcher_collaborators(researcher_id: int, db: Session = Depends(get_db)):
    return collaboration_service.get_researcher_collaborators(db, researcher_id)
