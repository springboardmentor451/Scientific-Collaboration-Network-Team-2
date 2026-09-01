import argparse
from getpass import getpass

from app.core.database import SessionLocal
from app.models.user import User
from app.Utils.auth import hash_password
from app.Schemas.user import validate_email, validate_password

def main():
    parser = argparse.ArgumentParser(description="Create or promote a secure SCNA Admin account.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="SCNA Administrator")
    args = parser.parse_args()
    email = validate_email(args.email)
    password = getpass("Admin password: ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation: raise SystemExit("Passwords do not match.")
    validate_password(password)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.role = "System Admin"; user.approval_status = "Approved"; user.is_active = True; user.password = hash_password(password); user.full_name = args.name
            action = "updated"
        else:
            user = User(full_name=args.name, email=email, password=hash_password(password), role="System Admin", approval_status="Approved", is_active=True)
            db.add(user); action = "created"
        db.commit()
        print(f"Admin account {action}: {email}")
    finally:
        db.close()

if __name__ == "__main__": main()
