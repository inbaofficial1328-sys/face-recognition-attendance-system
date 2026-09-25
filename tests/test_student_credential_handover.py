import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.dependencies import get_db
from backend.app.core.security import hash_password, verify_password
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.models.user import User
from backend.app.models.department import Department
from backend.app.models.academic_class import AcademicClass
from backend.app.models.student import Student


@pytest.fixture
def test_environment(monkeypatch):
    monkeypatch.setenv("ENABLE_STUDENT_REGISTRATION", "true")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        admin = User(
            login_id="handover_test_admin",
            full_name="Handover Test Admin",
            password_hash=hash_password("AdminTestPassword123"),
            role="ADMIN",
            is_active=True,
            must_change_password=False,
        )

        department = Department(
            code="IT",
            name="Information Technology",
        )

        db.add_all([admin, department])
        db.flush()

        academic_class = AcademicClass(
            department_id=department.id,
            name="Information Technology",
            section="A",
            semester=5,
        )

        db.add(academic_class)
        db.commit()

        class_id = academic_class.id

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client, engine, class_id
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_student_credential_handover(test_environment):
    client, engine, class_id = test_environment

    # Authenticate the administrator.
    login = client.post(
        "/api/auth/login",
        json={
            "login_id": "handover_test_admin",
            "password": "AdminTestPassword123",
        },
    )

    assert login.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }

    # Register a student.
    registration = client.post(
        "/api/students/",
        headers=headers,
        json={
            "login_id": "handover_test_student",
            "full_name": "Handover Test Student",
            "academic_class_id": class_id,
            "college_id": "HANDOVER001",
            "registration_number": "REGHANDOVER001",
        },
    )

    assert registration.status_code == 201

    data = registration.json()

    temporary_password = data["temporary_password"]

    assert len(temporary_password) >= 20

    # Sensitive responses must not be cached.
    assert "no-store" in registration.headers["cache-control"]
    assert registration.headers["pragma"] == "no-cache"
    assert registration.headers["referrer-policy"] == "no-referrer"

    # Verify the student account.
    with Session(engine) as db:
        user = db.query(User).filter_by(
            login_id="handover_test_student"
        ).one()

        student = db.query(Student).filter_by(
            user_id=user.id
        ).one()

        assert user.must_change_password is True
        assert user.role == "STUDENT"

        assert verify_password(
            temporary_password,
            user.password_hash,
        )

        assert student.academic_class_id == class_id

    # Student listings must not contain credentials.
    listing = client.get(
        "/api/students/",
        headers=headers,
    )

    assert listing.status_code == 200

    listing_text = listing.text.lower()

    assert "temporary_password" not in listing_text
    assert "password_hash" not in listing_text
    assert temporary_password not in listing.text

    # The credential must not appear in the ordinary
    # student object within the registration response.
    assert "temporary_password" not in data["student"]
    assert "password_hash" not in data["student"]