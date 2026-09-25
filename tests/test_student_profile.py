
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
from backend.app.models.student import Student


@pytest.fixture
def profile_environment():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        admin = User(
            login_id="profile_test_admin",
            full_name="Profile Test Admin",
            password_hash=hash_password("AdminTestPassword123"),
            role="ADMIN",
            is_active=True,
            must_change_password=False,
        )

        student_user = User(
            login_id="profile_test_student",
            full_name="Profile Test Student",
            password_hash=hash_password("StudentTestPassword123"),
            role="STUDENT",
            is_active=True,
            must_change_password=False,
        )

        db.add_all([admin, student_user])
        db.flush()

        student = Student(
            user_id=student_user.id,
            college_id="PROFILE001",
            registration_number="REGPROFILE001",
            department="Information Technology",
            class_name="Information Technology",
            semester=5,
        )

        db.add(student)
        db.commit()
        student_id = student.id

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client, student_id
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


def test_student_profile_access(profile_environment):
    client, student_id = profile_environment

    admin_headers = login(
        client,
        "profile_test_admin",
        "AdminTestPassword123",
    )

    # An administrator can retrieve an existing student.
    response = client.get(
        f"/api/students/{student_id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    profile = response.json()

    assert profile["id"] == student_id
    assert profile["college_id"] == "PROFILE001"
    assert profile["registration_number"] == "REGPROFILE001"

    # Ordinary profile responses must exclude credentials.
    assert "password_hash" not in response.text
    assert "temporary_password" not in response.text
    assert "StudentTestPassword123" not in response.text

    # A nonexistent student returns HTTP 404.
    missing = client.get(
        "/api/students/999999999",
        headers=admin_headers,
    )

    assert missing.status_code == 404

    # Students cannot access the administrative profile API.
    student_headers = login(
        client,
        "profile_test_student",
        "StudentTestPassword123",
    )

    forbidden = client.get(
        f"/api/students/{student_id}",
        headers=student_headers,
    )

    assert forbidden.status_code == 403

    # Unauthenticated requests are rejected.
    unauthorized = client.get(
        f"/api/students/{student_id}",
    )

    assert unauthorized.status_code == 401


def test_admin_can_update_student_profile(profile_environment):
    client, student_id = profile_environment

    admin_headers = login(
        client,
        "profile_test_admin",
        "AdminTestPassword123",
    )

    # Update the student's phone number.
    response = client.patch(
        f"/api/students/{student_id}",
        headers=admin_headers,
        json={
            "phone_number": "9876543210",
        },
    )

    assert response.status_code == 200
    assert response.json()["phone_number"] == "9876543210"

    # Verify that the change was saved.
    profile = client.get(
        f"/api/students/{student_id}",
        headers=admin_headers,
    )

    assert profile.status_code == 200
    assert profile.json()["phone_number"] == "9876543210"

    # Registration identifiers remain unchanged.
    assert profile.json()["college_id"] == "PROFILE001"
    assert (
        profile.json()["registration_number"]
        == "REGPROFILE001"
    )

    # An invalid academic class must be rejected.
    invalid_class = client.patch(
        f"/api/students/{student_id}",
        headers=admin_headers,
        json={
            "academic_class_id": 999999,
        },
    )

    assert invalid_class.status_code == 404

    # A nonexistent student cannot be updated.
    missing_student = client.patch(
        "/api/students/999999",
        headers=admin_headers,
        json={
            "phone_number": "1234567890",
        },
    )

    assert missing_student.status_code == 404

        # Password-related fields must be rejected.
    protected = client.patch(
        f"/api/students/{student_id}",
        headers=admin_headers,
        json={
            "password_hash": "should-not-be-accepted",
        },
    )

    assert protected.status_code == 422

    errors = protected.json()["detail"]

    assert any(
        error["type"] == "extra_forbidden"
        and "password_hash" in error["loc"]
        for error in errors
    )


def test_admin_can_reassign_academic_class(profile_environment):
    from sqlalchemy.orm import Session

    from backend.app.models.department import Department
    from backend.app.models.academic_class import AcademicClass

    client, student_id = profile_environment

    # Use the isolated database configured by the fixture.
    from backend.app.core.dependencies import get_db

    override = app.dependency_overrides[get_db]

    db_generator = override()
    db = next(db_generator)

    try:
        department = Department(
            code="CSE",
            name="Computer Science",
        )

        db.add(department)
        db.flush()

        academic_class = AcademicClass(
            department_id=department.id,
            name="Computer Science",
            section="B",
            semester=6,
        )

        db.add(academic_class)
        db.commit()

        class_id = academic_class.id
    finally:
        db_generator.close()

    admin_headers = login(
        client,
        "profile_test_admin",
        "AdminTestPassword123",
    )

    response = client.patch(
        f"/api/students/{student_id}",
        headers=admin_headers,
        json={
            "academic_class_id": class_id,
        },
    )

    assert response.status_code == 200

    profile = response.json()

    assert profile["academic_class_id"] == class_id
    assert profile["department"] == "Computer Science"
    assert profile["class_name"] == "Computer Science"
    assert profile["semester"] == 6

    # Confirm that the updated information was saved.
    saved = client.get(
        f"/api/students/{student_id}",
        headers=admin_headers,
    )

    assert saved.status_code == 200
    assert saved.json()["academic_class_id"] == class_id
    assert saved.json()["semester"] == 6


def test_student_update_validation(profile_environment):
    client, student_id = profile_environment

    admin_headers = login(
        client,
        "profile_test_admin",
        "AdminTestPassword123",
    )

    # Academic class cannot be cleared.
    null_class = client.patch(
        f"/api/students/{student_id}",
        headers=admin_headers,
        json={"academic_class_id": None},
    )

    assert null_class.status_code == 422

    # Registration identifiers are protected.
    protected = client.patch(
        f"/api/students/{student_id}",
        headers=admin_headers,
        json={"college_id": "CHANGED001"},
    )

    assert protected.status_code == 422

    # Confirm that the original identifier remains unchanged.
    profile = client.get(
        f"/api/students/{student_id}",
        headers=admin_headers,
    )

    assert profile.status_code == 200
    assert profile.json()["college_id"] == "PROFILE001"
