from sqlalchemy.orm import Session

from app.repositories import audit as audit_repo


def list_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
    path_contains: str | None = None,
):
    return audit_repo.get_logs(db, skip, limit, user_id, path_contains)
