from sqlalchemy.orm import Session

from app.models.conference import Conference, ConferenceParticipation


def get_conference(db: Session, conference_id: int):
    return db.query(Conference).filter(Conference.id == conference_id).first()


def get_conferences(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Conference).offset(skip).limit(limit).all()


def create_conference(db: Session, data: dict):
    db_conference = Conference(**data)
    db.add(db_conference)
    db.commit()
    db.refresh(db_conference)
    return db_conference


def update_conference(db: Session, conference_id: int, data: dict):
    db_conference = get_conference(db, conference_id)
    if not db_conference:
        return None
    for key, value in data.items():
        setattr(db_conference, key, value)
    db.commit()
    db.refresh(db_conference)
    return db_conference


def delete_conference(db: Session, conference_id: int):
    db_conference = get_conference(db, conference_id)
    if not db_conference:
        return None
    db.delete(db_conference)
    db.commit()
    return db_conference


def get_participation(db: Session, participation_id: int):
    return (
        db.query(ConferenceParticipation)
        .filter(ConferenceParticipation.id == participation_id)
        .first()
    )


def get_participations(
    db: Session, conference_id: int | None = None, researcher_id: int | None = None
):
    query = db.query(ConferenceParticipation)
    if conference_id:
        query = query.filter(ConferenceParticipation.conference_id == conference_id)
    if researcher_id:
        query = query.filter(ConferenceParticipation.researcher_id == researcher_id)
    return query.all()


def create_participation(db: Session, data: dict):
    db_participation = ConferenceParticipation(**data)
    db.add(db_participation)
    db.commit()
    db.refresh(db_participation)
    return db_participation


def update_participation(db: Session, participation_id: int, data: dict):
    db_participation = get_participation(db, participation_id)
    if not db_participation:
        return None
    for key, value in data.items():
        setattr(db_participation, key, value)
    db.commit()
    db.refresh(db_participation)
    return db_participation


def delete_participation(db: Session, participation_id: int):
    db_participation = get_participation(db, participation_id)
    if not db_participation:
        return None
    db.delete(db_participation)
    db.commit()
    return db_participation
