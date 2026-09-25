from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_admin_dashboard_requires_authentication():
    response = client.get("/api/admin/dashboard")

    assert response.status_code == 401


def test_current_user_requires_authentication():
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_login_rejects_unknown_user():
    response = client.post(
        "/api/auth/login",
        json={
            "login_id": "nonexistent_test_user",
            "password": "InvalidPassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid login credentials"

from pathlib import Path


def login_as(login_id: str, password_file: str):
    password = Path(password_file).read_text(
        encoding="utf-8"
    ).strip()

    return client.post(
        "/api/auth/login",
        json={
            "login_id": login_id,
            "password": password,
        },
    )


def test_admin_can_access_dashboard():
    login_response = login_as(
        "demo_admin",
        "demo_admin_password.txt",
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"


def test_student_cannot_access_admin_dashboard():
    login_response = login_as(
        "demo_student",
        "demo_student_password.txt",
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403