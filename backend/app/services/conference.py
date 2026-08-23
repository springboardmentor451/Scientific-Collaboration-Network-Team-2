from sqlalchemy.orm import Session

from app.repositories import conference as conference_repo


def create_new_conference(db: Session, conference):
    return conference_repo.create_conference(db, conference.model_dump())


def get_conference_by_id(db: Session, conference_id: int):
    conference = conference_repo.get_conference(db, conference_id)
    if not conference:
        raise ValueError("Conference not found")
    return conference


def list_conferences(db: Session, skip: int = 0, limit: int = 100):
    return conference_repo.get_conferences(db, skip, limit)


def update_existing_conference(db: Session, conference_id: int, conference_update):
    update_data = conference_update.model_dump(exclude_unset=True)
    updated = conference_repo.update_conference(db, conference_id, update_data)
    if not updated:
        raise ValueError("Conference not found")
    return updated


def delete_existing_conference(db: Session, conference_id: int):
    deleted = conference_repo.delete_conference(db, conference_id)
    if not deleted:
        raise ValueError("Conference not found")
    return deleted


def register_participation(db: Session, participation):
    if not conference_repo.get_conference(db, participation.conference_id):
        raise ValueError("Conference not found")
    return conference_repo.create_participation(db, participation.model_dump())


def list_participations(
    db: Session, conference_id: int | None = None, researcher_id: int | None = None
):
    return conference_repo.get_participations(db, conference_id, researcher_id)


def update_existing_participation(db: Session, participation_id: int, participation_update):
    update_data = participation_update.model_dump(exclude_unset=True)
    updated = conference_repo.update_participation(db, participation_id, update_data)
    if not updated:
        raise ValueError("Participation record not found")
    return updated


def delete_existing_participation(db: Session, participation_id: int):
    deleted = conference_repo.delete_participation(db, participation_id)
    if not deleted:
        raise ValueError("Participation record not found")
    return deleted
