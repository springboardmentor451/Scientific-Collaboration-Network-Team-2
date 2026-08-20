from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.security import get_password_hash
from backend.app.models.users import User, UserRole
from backend.app.db.base import Base
from backend.app.db.session import engine

def init_db(db: Session) -> None:
    # Create tables if they do not exist (useful for dev and compose)
    Base.metadata.create_all(bind=engine)
    
    # Create default admin user if not exists
    admin = db.query(User).filter(User.email == "admin@scna.org").first()
    if not admin:
        admin = User(
            email="admin@scna.org",
            password_hash=get_password_hash("admin"),
            role=UserRole.system_admin,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("Superuser admin@scna.org created.")
    else:
        print("Superuser admin@scna.org already exists.")
