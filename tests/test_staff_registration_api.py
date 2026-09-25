
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
def staff_api_environment(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        db.add_all([
            User(
                login_id="staff_api_admin",
                full_name="Staff API Admin",
                password_hash=hash_password("AdminTestPassword123"),
                role="ADMIN",
                is_active=True,
                must_change_password=False,
            ),
            User(
                login_id="staff_api_student",
                full_name="Staff API Student",
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

    monkeypatch.delenv("ENABLE_STAFF_REGISTRATION", raising=False)

    try:
        with TestClient(app) as client:
            yield client, monkeypatch
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def staff_login(client, login_id, password):
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


def test_staff_registration_access_control(staff_api_environment):
    client, monkeypatch = staff_api_environment

    payload = {
        "login_id": "new_teacher",
        "full_name": "New Teacher",
        "role": "TEACHER",
    }

    # Registration is disabled by default.
    admin_headers = staff_login(
        client,
        "staff_api_admin",
        "AdminTestPassword123",
    )

    disabled = client.post(
        "/api/staff/",
        json=payload,
        headers=admin_headers,
    )

    assert disabled.status_code == 503

    # Enable registration only inside this isolated test.
    monkeypatch.setenv("ENABLE_STAFF_REGISTRATION", "true")

    # Unauthenticated requests must be rejected.
    unauthorized = client.post(
        "/api/staff/",
        json=payload,
    )

    assert unauthorized.status_code == 401

    # Students must not create staff accounts.
    student_headers = staff_login(
        client,
        "staff_api_student",
        "StudentTestPassword123",
    )

    forbidden = client.post(
        "/api/staff/",
        json=payload,
        headers=student_headers,
    )

    assert forbidden.status_code == 403

    # Administrators can create staff accounts.
    created = client.post(
        "/api/staff/",
        json=payload,
        headers=admin_headers,
    )

    assert created.status_code == 201

    result = created.json()

    assert result["staff"]["role"] == "TEACHER"
    assert result["staff"]["must_change_password"] is True
    assert result["temporary_password"]
    assert "password_hash" not in result["staff"]

    assert created.headers["cache-control"].startswith("no-store")

    # Duplicate login IDs must be rejected.
    duplicate = client.post(
        "/api/staff/",
        json=payload,
        headers=admin_headers,
    )

    assert duplicate.status_code == 409


def test_staff_must_change_temporary_password(staff_api_environment):
    client, monkeypatch = staff_api_environment

    monkeypatch.setenv(
        "ENABLE_STAFF_REGISTRATION",
        "true",
    )

    admin_headers = staff_login(
        client,
        "staff_api_admin",
        "AdminTestPassword123",
    )

    # Register a new staff member.
    created = client.post(
        "/api/staff/",
        json={
            "login_id": "password_test_teacher",
            "full_name": "Password Test Teacher",
            "role": "TEACHER",
        },
        headers=admin_headers,
    )

    assert created.status_code == 201

    temporary_password = created.json()[
        "temporary_password"
    ]

    # Log in using the temporary password.
    teacher_headers = staff_login(
        client,
        "password_test_teacher",
        temporary_password,
    )

    # Protected access must be blocked.
    blocked = client.get(
        "/api/auth/me",
        headers=teacher_headers,
    )

    assert blocked.status_code == 403

    # Change the temporary password.
    changed = client.post(
        "/api/auth/change-password",
        headers=teacher_headers,
        json={
            "current_password": temporary_password,
            "new_password": "NewTeacherPassword123!",
        },
    )

    assert changed.status_code == 200

    # Log in again using the new password.
    new_headers = staff_login(
        client,
        "password_test_teacher",
        "NewTeacherPassword123!",
    )

    profile = client.get(
        "/api/auth/me",
        headers=new_headers,
    )

    assert profile.status_code == 200
    assert profile.json()["role"] == "TEACHER"


def test_staff_listing_access_control(staff_api_environment):
    client, monkeypatch = staff_api_environment

    monkeypatch.setenv(
        "ENABLE_STAFF_REGISTRATION",
        "true",
    )

    admin_headers = staff_login(
        client,
        "staff_api_admin",
        "AdminTestPassword123",
    )

    # Create a teacher and an HOD.
    for login_id, full_name, role in [
        ("listing_teacher", "Listing Teacher", "TEACHER"),
        ("listing_hod", "Listing HOD", "HOD"),
    ]:
        response = client.post(
            "/api/staff/",
            headers=admin_headers,
            json={
                "login_id": login_id,
                "full_name": full_name,
                "role": role,
            },
        )

        assert response.status_code == 201

    # Administrators can list staff.
    listed = client.get(
        "/api/staff/",
        headers=admin_headers,
    )

    assert listed.status_code == 200

    staff = listed.json()

    assert len(staff) == 2
    assert {item["role"] for item in staff} == {
        "TEACHER",
        "HOD",
    }

    # Sensitive credentials must not appear.
    for item in staff:
        assert "password_hash" not in item
        assert "temporary_password" not in item

    # Students cannot list staff.
    student_headers = staff_login(
        client,
        "staff_api_student",
        "StudentTestPassword123",
    )

    forbidden = client.get(
        "/api/staff/",
        headers=student_headers,
    )

    assert forbidden.status_code == 403

    # Authentication is mandatory.
    unauthorized = client.get("/api/staff/")

    assert unauthorized.status_code == 401


def test_staff_activation_and_deactivation(
    staff_api_environment,
):
    client, monkeypatch = staff_api_environment

    monkeypatch.setenv(
        "ENABLE_STAFF_REGISTRATION",
        "true",
    )

    admin_headers = staff_login(
        client,
        "staff_api_admin",
        "AdminTestPassword123",
    )

    # Create a teacher account.
    created = client.post(
        "/api/staff/",
        headers=admin_headers,
        json={
            "login_id": "status_test_teacher",
            "full_name": "Status Test Teacher",
            "role": "TEACHER",
        },
    )

    assert created.status_code == 201

    staff_id = created.json()["staff"]["id"]
    temporary_password = created.json()[
        "temporary_password"
    ]

    # Log in before deactivation.
    teacher_headers = staff_login(
        client,
        "status_test_teacher",
        temporary_password,
    )

    # Deactivate the teacher.
    deactivated = client.patch(
        f"/api/staff/{staff_id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )

    print("Deactivation status:", deactivated.status_code)
    print("Validation details:", deactivated.json())

    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    # An existing token must no longer work.
    blocked = client.get(
        "/api/auth/me",
        headers=teacher_headers,
    )

    assert blocked.status_code == 401

    # New login attempts must also fail.
    login_attempt = client.post(
        "/api/auth/login",
        json={
            "login_id": "status_test_teacher",
            "password": temporary_password,
        },
    )

    assert login_attempt.status_code == 401

    # Reactivate the teacher.
    reactivated = client.patch(
        f"/api/staff/{staff_id}/status",
        headers=admin_headers,
        json={"is_active": True},
    )

    assert reactivated.status_code == 200
    assert reactivated.json()["is_active"] is True

    # Login should work again.
    restored_headers = staff_login(
        client,
        "status_test_teacher",
        temporary_password,
    )

    assert restored_headers["Authorization"].startswith(
        "Bearer "
    )



def test_staff_status_protects_other_roles(
    staff_api_environment,
):
    client, monkeypatch = staff_api_environment

    from backend.app.core.dependencies import get_db
    from backend.app.models.user import User

    # Retrieve account IDs from the isolated test database.
    override = app.dependency_overrides[get_db]
    db_generator = override()
    db = next(db_generator)

    try:
        admin = db.query(User).filter_by(
            login_id="staff_api_admin"
        ).one()

        student = db.query(User).filter_by(
            login_id="staff_api_student"
        ).one()

        admin_id = admin.id
        student_id = student.id

    finally:
        db_generator.close()

    admin_headers = staff_login(
        client,
        "staff_api_admin",
        "AdminTestPassword123",
    )

    # The staff endpoint must not modify ADMIN accounts.
    admin_response = client.patch(
        f"/api/staff/{admin_id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )

    assert admin_response.status_code == 404

    # The staff endpoint must not modify STUDENT accounts.
    student_response = client.patch(
        f"/api/staff/{student_id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )

    assert student_response.status_code == 404

    # Invalid staff IDs must also be rejected.
    missing = client.patch(
        "/api/staff/999999/status",
        headers=admin_headers,
        json={"is_active": False},
    )

    assert missing.status_code == 404

    # Confirm the administrator can still access protected resources.
    dashboard = client.get(
        "/api/admin/dashboard",
        headers=admin_headers,
    )

    assert dashboard.status_code == 200
