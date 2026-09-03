from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_dashboard_summary_requires_authentication():
    response = client.get("/dashboard/summary")

    assert response.status_code == 401
