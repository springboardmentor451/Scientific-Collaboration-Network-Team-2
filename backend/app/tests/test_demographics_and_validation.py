import pytest
from fastapi.testclient import TestClient

def test_password_strength_validation(client: TestClient):
    # Weak passwords should fail validation with 422
    weak_passwords = [
        "short1!",        # Less than 8 chars
        "alllowercase1!",  # No uppercase
        "ALLUPPERCASE1!",  # No lowercase
        "NoDigitsHere!",  # No digits
        "NoSpecialChar1"  # No special char
    ]

    for passw in weak_passwords:
        response = client.post("/api/v1/auth/register", json={
            "email": "user@scna.org",
            "password": passw,
            "role": "researcher"
        })
        assert response.status_code == 422, f"Expected 422 for weak password: {passw}"

    # Valid strong password should succeed (201)
    response = client.post("/api/v1/auth/register", json={
        "email": "stronguser@scna.org",
        "password": "StrongP@ssword123",
        "role": "researcher"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "stronguser@scna.org"


def test_email_normalization_and_verification(client: TestClient):
    # Register with mixed case and whitespace
    response = client.post("/api/v1/auth/register", json={
        "email": "  Test.User@SCNA.ORG  ",
        "password": "StrongP@ssword123",
        "role": "researcher"
    })
    assert response.status_code == 201
    reg_data = response.json()
    assert reg_data["email"] == "test.user@scna.org"
    assert reg_data["is_verified"] is True
    assert reg_data["verification_token"] is None

    # Verify login succeeds with normalized email
    login_res = client.post("/api/v1/auth/login", data={
        "username": "TEST.USER@scna.org",
        "password": "StrongP@ssword123"
    })
    assert login_res.status_code == 200


def test_mobile_number_validation(client: TestClient):
    # Register researcher user
    reg = client.post("/api/v1/auth/register", json={
        "email": "mobileresearcher@scna.org",
        "password": "StrongP@ssword123",
        "role": "researcher"
    })
    user_id = reg.json()["id"]

    login_res = client.post("/api/v1/auth/login", data={
        "username": "mobileresearcher@scna.org",
        "password": "StrongP@ssword123"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Invalid mobile numbers (not 10 digits) should fail with 422
    invalid_mobiles = [
        "123456789",     # 9 digits
        "12345678901",   # 11 digits
        "+1987654321",   # includes +
        "98765-43210",   # includes hyphen
        "98765 43210",   # includes space
        "abcdefghij"     # letters
    ]

    for mob in invalid_mobiles:
        res = client.post("/api/v1/researchers/", headers=headers, json={
            "user_id": user_id,
            "full_name": "Test Mobile Researcher",
            "orcid_id": "0000-0002-1825-0001",
            "mobile_number": mob
        })
        assert res.status_code == 422, f"Expected 422 for invalid mobile: {mob}"

    # Valid 10-digit mobile number should succeed
    res = client.post("/api/v1/researchers/", headers=headers, json={
        "user_id": user_id,
        "full_name": "Test Mobile Researcher",
        "orcid_id": "0000-0002-1825-0001",
        "mobile_number": "9876543210",
        "gender": "female",
        "nationality": "Indian",
        "country": "India",
        "city": "Mumbai"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["mobile_number"] == "9876543210"
    assert data["gender"] == "female"
    assert data["nationality"] == "Indian"


def test_profile_completion_status(client: TestClient):
    reg = client.post("/api/v1/auth/register", json={
        "email": "completion@scna.org",
        "password": "StrongP@ssword123",
        "role": "researcher"
    })
    user_id = reg.json()["id"]

    login_res = client.post("/api/v1/auth/login", data={
        "username": "completion@scna.org",
        "password": "StrongP@ssword123"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    create_res = client.post("/api/v1/researchers/", headers=headers, json={
        "user_id": user_id,
        "full_name": "Dr. Alan Turing",
        "orcid_id": "0000-0002-1825-0002",
        "mobile_number": "1234567890",
        "gender": "male",
        "country": "UK",
        "city": "London",
        "skills": ["Cryptography", "Computing"],
        "research_interests": ["Artificial Intelligence"]
    })
    res_id = create_res.json()["id"]

    status_res = client.get(f"/api/v1/researchers/{res_id}/completion-status", headers=headers)
    assert status_res.status_code == 200
    comp_data = status_res.json()
    assert "completion_percentage" in comp_data
    assert comp_data["completion_percentage"] > 0


def test_global_search_endpoint(client: TestClient):
    reg = client.post("/api/v1/auth/register", json={
        "email": "searchuser@scna.org",
        "password": "StrongP@ssword123",
        "role": "researcher"
    })
    login_res = client.post("/api/v1/auth/login", data={
        "username": "searchuser@scna.org",
        "password": "StrongP@ssword123"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    client.post("/api/v1/researchers/", headers=headers, json={
        "user_id": reg.json()["id"],
        "full_name": "Prof. Quantum Explorer",
        "orcid_id": "0000-0002-1825-0003",
        "mobile_number": "9998887770"
    })

    client.post("/api/v1/publications/", headers=headers, json={
        "title": "Quantum Computing Mechanics in Graphs",
        "type": "journal_paper",
        "status": "published"
    })

    search_res = client.get("/api/v1/search?q=Quantum", headers=headers)
    assert search_res.status_code == 200
    data = search_res.json()
    assert "results" in data
    res_dict = data["results"]
    assert "researchers" in res_dict
    assert "publications" in res_dict
    assert len(res_dict["researchers"]) + len(res_dict["publications"]) > 0


def test_notifications_endpoint(client: TestClient):
    reg = client.post("/api/v1/auth/register", json={
        "email": "notifyuser@scna.org",
        "password": "StrongP@ssword123",
        "role": "researcher"
    })
    login_res = client.post("/api/v1/auth/login", data={
        "username": "notifyuser@scna.org",
        "password": "StrongP@ssword123"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Fetch notifications
    notif_res = client.get("/api/v1/notifications/", headers=headers)
    assert notif_res.status_code == 200

    unread_res = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread_res.status_code == 200
    assert "unread_count" in unread_res.json()
