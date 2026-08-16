"""
Adds a small set of memorable demo accounts (fixed emails/password) on top of
the randomly-seeded data, so it's easy to log in and try each role without
hunting through the Faker-generated emails.

Usage: python add_demo_accounts.py
"""
from passlib.hash import bcrypt

from app.database import SessionLocal
from app.models import Institution, Researcher, User, UserRole

DEMO_PASSWORD = "Password123!"

ACCOUNTS = [
    ("admin@researchsphere.dev", UserRole.SYSTEM_ADMIN, "System Administrator"),
    ("institution.admin@researchsphere.dev", UserRole.INSTITUTION_ADMIN, "Institution Admin Demo"),
    ("reviewer@researchsphere.dev", UserRole.REVIEWER, "Reviewer Demo"),
    ("researcher@researchsphere.dev", UserRole.RESEARCHER, "Researcher Demo"),
]


def run():
    db = SessionLocal()
    try:
        institution = db.query(Institution).first()
        for email, role, name in ACCOUNTS:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                print(f"skip (already exists): {email}")
                continue
            user = User(
                email=email,
                hashed_password=bcrypt.hash(DEMO_PASSWORD),
                role=role,
                is_verified=True,
                is_active=True,
            )
            db.add(user)
            db.flush()

            if role == UserRole.RESEARCHER:
                db.add(Researcher(
                    user_id=user.id,
                    institution_id=institution.id if institution else None,
                    full_name=name,
                    department="Computer Science",
                    academic_title="Researcher",
                ))
            db.commit()
            print(f"created: {email} / {DEMO_PASSWORD}  (role={role.value})")
    finally:
        db.close()


if __name__ == "__main__":
    run()
