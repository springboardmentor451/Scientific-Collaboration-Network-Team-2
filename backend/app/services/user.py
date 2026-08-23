from sqlalchemy.orm import Session

from app.repositories import user as user_repo


def get_user_by_id(db: Session, user_id: int):
    user = user_repo.get_user(db, user_id)
    if not user:
        raise ValueError("User not found")
    return user


def list_users(db: Session, skip: int = 0, limit: int = 100):
    return user_repo.get_users(db, skip, limit)


def update_existing_user(db: Session, user_id: int, user_update):
    update_data = user_update.model_dump(exclude_unset=True)
    updated = user_repo.update_user(db, user_id, update_data)
    if not updated:
        raise ValueError("User not found")
    return updated


def delete_existing_user(db: Session, user_id: int):
    deleted = user_repo.delete_user(db, user_id)
    if not deleted:
        raise ValueError("User not found")
    return deleted
