from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.repositories import project as project_repo


def _resolve_institutions(db: Session, institution_ids: list[int]) -> list[Institution]:
    if not institution_ids:
        return []
    institutions = db.query(Institution).filter(Institution.id.in_(institution_ids)).all()
    found_ids = {i.id for i in institutions}
    missing = set(institution_ids) - found_ids
    if missing:
        raise ValueError(f"Institution id(s) not found: {sorted(missing)}")
    return institutions


def create_new_project(db: Session, project):
    data = project.model_dump(exclude={"institution_ids"})
    institutions = _resolve_institutions(db, project.institution_ids)
    return project_repo.create_project(db, data, institutions)


def get_project_by_id(db: Session, project_id: int):
    project = project_repo.get_project(db, project_id)
    if not project:
        raise ValueError("Project not found")
    return project


def list_projects(db: Session, skip: int = 0, limit: int = 100, status: str | None = None):
    return project_repo.get_projects(db, skip, limit, status)


def update_existing_project(db: Session, project_id: int, project_update):
    update_data = project_update.model_dump(exclude_unset=True, exclude={"institution_ids"})

    institutions = None
    if project_update.institution_ids is not None:
        institutions = _resolve_institutions(db, project_update.institution_ids)

    updated = project_repo.update_project(db, project_id, update_data, institutions)
    if not updated:
        raise ValueError("Project not found")
    return updated


def delete_existing_project(db: Session, project_id: int):
    deleted = project_repo.delete_project(db, project_id)
    if not deleted:
        raise ValueError("Project not found")
    return deleted


def add_project_member(db: Session, project_id: int, researcher_id: int, role_in_project):
    if not project_repo.get_project(db, project_id):
        raise ValueError("Project not found")

    result = project_repo.add_member(db, project_id, researcher_id, role_in_project)
    if result is None:
        raise ValueError("Researcher is already a member of this project")
    return result


def remove_project_member(db: Session, project_id: int, researcher_id: int):
    if not project_repo.get_project(db, project_id):
        raise ValueError("Project not found")
    return project_repo.remove_member(db, project_id, researcher_id)
