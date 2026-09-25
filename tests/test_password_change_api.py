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

    initial_password = "InitialPassword123"

    with Session(engine) as db:
        user = User(
            login_id="isolated_password_student",
            full_name="Isolated Test Student",
            password_hash=hash_password(initial_password),
            role="STUDENT",
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
            yield test_client, engine
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_authenticated_password_change(client):
    test_client, engine = client

    initial_password = "InitialPassword123"
    new_password = "NewSecurePassword456"

    login = test_client.post(
        "/api/auth/login",
        json={
            "login_id": "isolated_password_student",
            "password": initial_password,
        },
    )

    assert login.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }

    incorrect = test_client.post(
        "/api/auth/change-password",
        headers=headers,
        json={
            "current_password": "IncorrectPassword123",
            "new_password": new_password,
        },
    )

    assert incorrect.status_code == 400

    changed = test_client.post(
        "/api/auth/change-password",
        headers=headers,
        json={
            "current_password": initial_password,
            "new_password": new_password,
        },
    )

    assert changed.status_code == 200

    old_login = test_client.post(
        "/api/auth/login",
        json={
            "login_id": "isolated_password_student",
            "password": initial_password,
        },
    )

    assert old_login.status_code == 401

    new_login = test_client.post(
        "/api/auth/login",
        json={
            "login_id": "isolated_password_student",
            "password": new_password,
        },
    )

    assert new_login.status_code == 200

    with Session(engine) as db:
        user = db.query(User).filter_by(
            login_id="isolated_password_student"
        ).one()

        assert user.must_change_password is False