from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.user import User
from app.Schemas.user import UserCreate
from app.Utils.auth import hash_password
from app.models.institution import Institution


def get_user_by_email(db: Session, email: str):
    normalized_email = str(email).strip().lower()
    return db.query(User).filter(func.lower(User.email) == normalized_email).first()


def create_user(db: Session, user: UserCreate):
    try:
        hashed_password = hash_password(user.password)

        institution = db.query(Institution).filter(func.lower(Institution.name) == user.institution.lower()).first() if user.institution else None
        db_user = User(
            full_name=user.full_name,
            email=user.email,
            password=hashed_password,
            role=user.role,
            approval_status="Pending",
            institution=user.institution,
            institution_id=institution.id if institution else None,
            department=user.department,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    except Exception as e:
        print("ERROR:", repr(e))
        raise
