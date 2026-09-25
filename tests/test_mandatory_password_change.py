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
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        user = User(
            login_id="mandatory_change_test",
            full_name="Mandatory Change Test",
            password_hash=hash_password("InitialPassword123"),
            role="ADMIN",
            is_active=True,
            must_change_password=True,
        )

        db.add(user)
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


def test_mandatory_password_change(client):
    # 1. Login must remain available.
    login = client.post(
        "/api/auth/login",
        json={
            "login_id": "mandatory_change_test",
            "password": "InitialPassword123",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 2. Protected resources must be blocked.
    blocked_profile = client.get(
        "/api/auth/me",
        headers=headers,
    )

    assert blocked_profile.status_code == 403
    assert "Password change required" in (
        blocked_profile.json()["detail"]
    )

    blocked_dashboard = client.get(
        "/api/admin/dashboard",
        headers=headers,
    )

    assert blocked_dashboard.status_code == 403
    assert "Password change required" in (
        blocked_dashboard.json()["detail"]
    )

    # 3. Password change must remain available.
    changed = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={
            "current_password": "InitialPassword123",
            "new_password": "UpdatedPassword456",
        },
    )

    assert changed.status_code == 200

    # 4. Protected resources must now be accessible.
    allowed_profile = client.get(
        "/api/auth/me",
        headers=headers,
    )

    assert allowed_profile.status_code == 200

    allowed_dashboard = client.get(
        "/api/admin/dashboard",
        headers=headers,
    )

    assert allowed_dashboard.status_code == 200

    # 5. Old password must no longer work.
    old_login = client.post(
        "/api/auth/login",
        json={
            "login_id": "mandatory_change_test",
            "password": "InitialPassword123",
        },
    )

    assert old_login.status_code == 401

    # 6. New password must work.
    new_login = client.post(
        "/api/auth/login",
        json={
            "login_id": "mandatory_change_test",
            "password": "UpdatedPassword456",
        },
    )

    assert new_login.status_code == 200