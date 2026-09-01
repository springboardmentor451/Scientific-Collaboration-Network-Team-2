import os
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["EMAIL_DELIVERY_MODE"] = "test"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.Routes.user import _code_hash


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def register(self, email="sahera@gmail.com", password="Sahera@123", full_name="Sahera Shaikh"):
        response = client.post(
            "/users/register",
            json={"full_name": full_name, "email": email, "password": password},
        )
        if response.status_code == 201:
            db = TestingSessionLocal()
            db.query(User).filter(User.email == email.lower()).update({User.approval_status: "Approved", User.email_verified: True})
            db.commit(); db.close()
        return response

    def test_registration_accepts_valid_email_domains(self):
        emails = [
            "sahera@gmail.com",
            "user@yahoo.com",
            "user@outlook.com",
            "researcher@example.com",
        ]
        for index, email in enumerate(emails):
            with self.subTest(email=email):
                response = self.register(email=email, full_name=f"Researcher {index}")
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.json()["email"], email)

    def test_registration_rejects_invalid_email(self):
        invalid_emails = ["sahera", "sahera@", "@gmail.com", "sahera@gmail", "sahera gmail.com"]
        for email in invalid_emails:
            with self.subTest(email=email):
                response = self.register(email=email)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["detail"], "Please enter a valid email address.")

    def test_registration_rejects_weak_password(self):
        cases = [
            ("Short@", "Password must be at least 8 characters long."),
            ("Sahera123", "Password must contain at least one special character."),
        ]
        for password, message in cases:
            with self.subTest(password=password):
                response = self.register(password=password)
                self.assertEqual(response.status_code, 422)
                self.assertIn(message, response.text)

    def test_email_verification_blocks_login_until_valid_code(self):
        response = client.post("/users/register", json={"full_name": "Verification User", "email": "verify@example.com", "password": "Verify@123"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(client.post("/users/login", json={"email": "verify@example.com", "password": "Verify@123"}).status_code, 403)
        db = TestingSessionLocal()
        user = db.query(User).filter_by(email="verify@example.com").first()
        user.verification_code_hash = _code_hash(user.email, "123456")
        user.verification_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        db.commit(); db.close()
        verified = client.post("/users/verify-email", json={"email": "verify@example.com", "code": "123456"})
        self.assertEqual(verified.status_code, 200)
        db = TestingSessionLocal(); db.query(User).filter_by(email="verify@example.com").update({User.approval_status: "Approved"}); db.commit(); db.close()
        self.assertEqual(client.post("/users/login", json={"email": "verify@example.com", "password": "Verify@123"}).status_code, 200)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.assertEqual(self.register(email="Sahera@Gmail.com").status_code, 201)
        response = self.register(email="sahera@gmail.com")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Email already registered.")

    def test_login_returns_the_matching_user(self):
        first = self.register().json()
        second = self.register(
            email="zoyashaikh@yahoo.com",
            password="Zoya@1234",
            full_name="Zoya Shaikh",
        ).json()

        response = client.post(
            "/users/login",
            json={"email": "ZOYASHAIKH@YAHOO.COM", "password": "Zoya@1234"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["id"], second["id"])
        self.assertNotEqual(response.json()["user"]["id"], first["id"])

    def test_login_rejects_invalid_credentials_or_input(self):
        self.register()
        cases = [
            ({"email": "sahera@gmail.com", "password": "Wrong@123"}, 401),
            ({"email": "unknown@gmail.com", "password": "Sahera@123"}, 401),
            ({"email": "invalid-email", "password": "Sahera@123"}, 422),
            ({"email": "", "password": "Sahera@123"}, 422),
            ({"email": "sahera@gmail.com", "password": ""}, 422),
        ]
        for payload, expected_status in cases:
            with self.subTest(payload=payload):
                response = client.post("/users/login", json=payload)
                self.assertEqual(response.status_code, expected_status)
                if expected_status == 401:
                    self.assertEqual(response.json()["detail"], "Invalid email or password.")

    def test_complete_real_user_workflow_and_ownership(self):
        first = self.register().json()
        self.register(email="zoya@gmail.com", password="Zoya@1234", full_name="Zoya Shaikh")
        first_token = client.post("/users/login", json={"email":"sahera@gmail.com","password":"Sahera@123"}).json()["access_token"]
        second_token = client.post("/users/login", json={"email":"zoya@gmail.com","password":"Zoya@1234"}).json()["access_token"]
        first_headers, second_headers = {"Authorization":f"Bearer {first_token}"}, {"Authorization":f"Bearer {second_token}"}

        researcher = client.post("/researchers", headers=first_headers, json={"name":"Sahera Shaikh","email":"sahera@gmail.com","department":"Computer Science","institution":"SCNA University","field":"Artificial Intelligence","skills":["Python"],"research_interests":["Networks"]}).json()
        publication = client.post("/publications", headers=first_headers, json={"title":"Real Network Study","authors":"Sahera Shaikh","research_area":"Network Science","venue":"SCNA Journal","publication_year":2026}).json()
        self.assertEqual(client.delete(f"/publications/{publication['id']}", headers=second_headers).status_code, 403)

        request = client.post("/collaborations/request", headers=second_headers, json={"researcher_id":researcher["id"],"message":"Let us collaborate"}).json()
        self.assertEqual(client.put(f"/collaborations/requests/{request['id']}/accept", headers=second_headers).status_code, 403)
        self.assertEqual(client.put(f"/collaborations/requests/{request['id']}/accept", headers=first_headers).status_code, 200)
        report = client.get("/reports/my", headers=first_headers).json()
        self.assertEqual(report["publication_count"], 1)
        self.assertEqual(report["collaboration_count"], 1)
        self.assertEqual(first["id"], researcher["user_id"])

    def test_admin_only_real_data_management(self):
        admin = self.register(email="admin@example.com", password="Admin@123", full_name="SCNA Admin").json()
        db = TestingSessionLocal(); db_user = db.query(__import__("app.models.user", fromlist=["User"]).User).filter_by(id=admin["id"]).first(); db_user.role="Admin"; db.commit(); db.close()
        token = client.post("/users/login", json={"email":"admin@example.com","password":"Admin@123"}).json()["access_token"]
        headers = {"Authorization":f"Bearer {token}"}
        institution = client.post("/institutions", headers=headers, json={"name":"SCNA University","short_name":"SCNAU","location":"Pune","research_areas":["AI"]})
        self.assertEqual(institution.status_code, 201)
        conference = client.post("/conferences", headers=headers, json={"title":"SCNA Research Summit","topic":"Networks","location":"Pune","starts_at":"2027-01-01T10:00:00Z"})
        self.assertEqual(conference.status_code, 201)
        self.assertEqual(client.get("/admin/statistics", headers=headers).json()["total_institutions"], 1)

    def test_admin_profile_is_read_only_but_password_change_is_secure(self):
        admin = self.register(email="secure-admin@example.com", password="Admin@123", full_name="Secure Admin").json()
        db = TestingSessionLocal()
        db_user = db.query(User).filter_by(id=admin["id"]).first()
        db_user.role = "System Admin"
        db.commit(); db.close()
        token = client.post("/users/login", json={"email": "secure-admin@example.com", "password": "Admin@123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        self.assertEqual(client.put("/users/me", headers=headers, json={"full_name": "Changed"}).status_code, 403)
        self.assertEqual(client.post("/users/me/password/verify", headers=headers, json={"current_password": "Admin@123"}).status_code, 200)
        self.assertEqual(client.put("/users/me/password", headers=headers, json={"current_password": "Wrong@123", "new_password": "NewAdmin@123"}).status_code, 400)
        self.assertEqual(client.put("/users/me/password", headers=headers, json={"current_password": "Admin@123", "new_password": "NewAdmin@123"}).status_code, 200)
        self.assertEqual(client.post("/users/login", json={"email": "secure-admin@example.com", "password": "NewAdmin@123"}).status_code, 200)

    def test_assistant_requires_authentication_and_handles_local_model_availability(self):
        self.assertEqual(client.post("/assistant/chat", json={"message": "List my publications"}).status_code, 401)
        self.register(email="assistant@example.com", password="Assistant@123", full_name="Assistant User")
        token = client.post("/users/login", json={"email": "assistant@example.com", "password": "Assistant@123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        self.assertEqual(client.post("/assistant/chat", headers=headers, json={"message": "   "}).status_code, 422)
        with patch("app.Routes.assistant.ask_ollama", return_value="No publications are available in your records."):
            response = client.post("/assistant/chat", headers=headers, json={"message": "Summarize my publications"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "Local Ollama model using permitted SCNA records")
        with patch("app.Routes.assistant.ask_ollama", side_effect=RuntimeError("offline")):
            response = client.post("/assistant/chat", headers=headers, json={"message": "Summarize my publications"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "The assistant is temporarily unavailable. Please try again.")


if __name__ == "__main__":
    unittest.main()
