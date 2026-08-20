import pytest
from fastapi.testclient import TestClient

def test_auth_workflow(client: TestClient):
    # 1. Register a system admin
    response = client.post("/api/v1/auth/register", json={
        "email": "testadmin@scna.org",
        "password": "StrongP@ssword123",
        "role": "system_admin"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "testadmin@scna.org"
    assert response.json()["role"] == "system_admin"

    # 2. Login
    response = client.post("/api/v1/auth/login", data={
        "username": "testadmin@scna.org",
        "password": "StrongP@ssword123"
    })
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Me
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "testadmin@scna.org"


def test_researcher_and_publications(client: TestClient):
    # 1. Register researcher
    client.post("/api/v1/auth/register", json={
        "email": "researcher@scna.org",
        "password": "StrongP@ssword123",
        "role": "researcher"
    })
    
    # Login
    response = client.post("/api/v1/auth/login", data={
        "username": "researcher@scna.org",
        "password": "StrongP@ssword123"
    })
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get User profile
    user_me = client.get("/api/v1/users/me", headers=headers).json()
    user_id = user_me["id"]

    # Create Researcher profile
    response = client.post("/api/v1/researchers/", headers=headers, json={
        "user_id": user_id,
        "full_name": "Dr. Marie Curie",
        "orcid_id": "0000-0002-1825-0097",
        "skills": ["Chemistry", "Physics"],
        "research_interests": ["Radioactivity", "Polonium"]
    })
    assert response.status_code == 201
    researcher_id = response.json()["id"]

    # Create Publication
    response = client.post("/api/v1/publications/", headers=headers, json={
        "title": "On Radioactivity of Uranium",
        "abstract": "Analysis of radioactivity in pitchblende uranium ores.",
        "type": "journal_paper",
        "status": "published",
        "venue": "Comptes Rendus",
        "doi": "10.1000/xyz123"
    })
    assert response.status_code == 201
    pub_id = response.json()["id"]

    # Verify Network graph
    response = client.get("/api/v1/network/graph", headers=headers)
    assert response.status_code == 200
    graph_data = response.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data

    # Export Reports
    response = client.get("/api/v1/reports/export?format=xlsx", headers=headers)
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=collaboration_report.xlsx"

    response = client.get("/api/v1/reports/export?format=pdf", headers=headers)
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=collaboration_report.pdf"

