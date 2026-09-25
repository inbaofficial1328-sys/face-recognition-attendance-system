import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.dependencies import get_db
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.models.user import User


@pytest.fixture
def client(monkeypatch):
    # Keep registration disabled for this checkpoint.
    monkeypatch.delenv("ENABLE_STUDENT_REGISTRATION", raising=False)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        db.add_all([
            User(
                login_id="registration_test_admin",
                full_name="Registration Test Admin",
                password_hash=hash_password("AdminTestPassword123"),
                role="ADMIN",
                is_active=True,
                must_change_password=False,
            ),
            User(
                login_id="registration_test_student",
                full_name="Registration Test Student",
                password_hash=hash_password("StudentTestPassword123"),
                role="STUDENT",
                is_active=True,
                must_change_password=False,
            ),
        ])
        db.commit()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def login(client, login_id, password):
    response = client.post(
        "/api/auth/login",
        json={
            "login_id": login_id,
            "password": password,
        },
    )

    assert response.status_code == 200

    return {
        "Authorization": (
            f"Bearer {response.json()['access_token']}"
        )
    }


def test_registration_access_control(client):
    student_data = {
        "login_id": "new_security_test_student",
        "full_name": "New Security Test Student",
        "academic_class_id": 1,
        "college_id": "SECURITY002",
        "registration_number": "REGSECURITY002",
    }

    # Unauthenticated users must be blocked.
    unauthenticated = client.post(
        "/api/students/",
        json=student_data,
    )
    assert unauthenticated.status_code == 401

    # STUDENT users must be blocked.
    student_headers = login(
        client,
        "registration_test_student",
        "StudentTestPassword123",
    )

    student_response = client.post(
        "/api/students/",
        headers=student_headers,
        json=student_data,
    )
    assert student_response.status_code == 403

    # ADMIN authentication succeeds, but registration
    # remains disabled until credential delivery is tested.
    admin_headers = login(
        client,
        "registration_test_admin",
        "AdminTestPassword123",
    )

    admin_response = client.post(
        "/api/students/",
        headers=admin_headers,
        json=student_data,
    )
    assert admin_response.status_code == 503