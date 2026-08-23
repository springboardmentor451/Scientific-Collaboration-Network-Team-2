from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.models.project import ResearchProject, project_members
from app.models.researcher import Researcher


def get_project(db: Session, project_id: int):
    return db.query(ResearchProject).filter(ResearchProject.id == project_id).first()


def get_projects(db: Session, skip: int = 0, limit: int = 100, status: str | None = None):
    query = db.query(ResearchProject)
    if status:
        query = query.filter(ResearchProject.status == status)
    return query.offset(skip).limit(limit).all()


def create_project(db: Session, data: dict, institutions: list[Institution]):
    db_project = ResearchProject(**data)
    db_project.institutions = institutions
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def update_project(
    db: Session, project_id: int, data: dict, institutions: list[Institution] | None = None
):
    db_project = get_project(db, project_id)
    if not db_project:
        return None

    for key, value in data.items():
        setattr(db_project, key, value)

    if institutions is not None:
        db_project.institutions = institutions

    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: int):
    db_project = get_project(db, project_id)
    if not db_project:
        return None

    db.delete(db_project)
    db.commit()
    return db_project


def add_member(db: Session, project_id: int, researcher_id: int, role_in_project: str | None):
    exists = db.execute(
        project_members.select().where(
            project_members.c.project_id == project_id,
            project_members.c.researcher_id == researcher_id,
        )
    ).first()
    if exists:
        return None

    db.execute(
        project_members.insert().values(
            project_id=project_id,
            researcher_id=researcher_id,
            role_in_project=role_in_project,
        )
    )
    db.commit()
    return get_project(db, project_id)


def remove_member(db: Session, project_id: int, researcher_id: int):
    db.execute(
        project_members.delete().where(
            project_members.c.project_id == project_id,
            project_members.c.researcher_id == researcher_id,
        )
    )
    db.commit()
    return get_project(db, project_id)


def get_project_member_roles(db: Session, project_id: int):
    rows = db.execute(
        project_members.select().where(project_members.c.project_id == project_id)
    ).fetchall()
    return [
        {"researcher_id": r.researcher_id, "role_in_project": r.role_in_project}
        for r in rows
    ]
