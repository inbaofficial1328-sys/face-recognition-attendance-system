
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.dependencies import get_db
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.models.academic_class import AcademicClass
from backend.app.models.department import Department
from backend.app.models.teacher_assignment import TeacherAssignment
from backend.app.models.user import User


@pytest.fixture
def attendance_api_environment():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        department = Department(
            name="Information Technology",
            code="IT",
        )
        db.add(department)
        db.flush()

        academic_class = AcademicClass(
            department_id=department.id,
            name="IT",
            section="A",
            semester=5,
        )
        db.add(academic_class)
        db.flush()

        teacher = User(
            login_id="attendance_teacher",
            full_name="Attendance Teacher",
            password_hash=hash_password("TeacherTestPassword123"),
            role="TEACHER",
            is_active=True,
            must_change_password=False,
        )

        unassigned_teacher = User(
            login_id="unassigned_teacher",
            full_name="Unassigned Teacher",
            password_hash=hash_password("TeacherTestPassword123"),
            role="TEACHER",
            is_active=True,
            must_change_password=False,
        )

        student = User(
            login_id="attendance_student",
            full_name="Attendance Student",
            password_hash=hash_password("StudentTestPassword123"),
            role="STUDENT",
            is_active=True,
            must_change_password=False,
        )

        db.add_all([teacher, unassigned_teacher, student])
        db.flush()

        db.add(
            TeacherAssignment(
                teacher_id=teacher.id,
                academic_class_id=academic_class.id,
            )
        )

        class_id = academic_class.id
        teacher_id = teacher.id

        db.commit()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client, class_id, teacher_id
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


def payload(class_id, attendance_date=None):
    return {
        "academic_class_id": class_id,
        "attendance_date": (
            attendance_date or date.today()
        ).isoformat(),
        "period_number": 2,
    }


def test_assigned_teacher_creates_attendance_session(
    attendance_api_environment,
):
    client, class_id, teacher_id = attendance_api_environment

    headers = login(
        client,
        "attendance_teacher",
        "TeacherTestPassword123",
    )

    response = client.post(
        "/api/attendance-sessions/",
        headers=headers,
        json=payload(class_id),
    )

    assert response.status_code == 201
    assert response.json()["teacher_id"] == teacher_id
    assert response.json()["academic_class_id"] == class_id
    assert response.json()["status"] == "OPEN"


def test_duplicate_attendance_session(
    attendance_api_environment,
):
    client, class_id, _ = attendance_api_environment

    headers = login(
        client,
        "attendance_teacher",
        "TeacherTestPassword123",
    )

    first = client.post(
        "/api/attendance-sessions/",
        headers=headers,
        json=payload(class_id),
    )

    assert first.status_code == 201

    duplicate = client.post(
        "/api/attendance-sessions/",
        headers=headers,
        json=payload(class_id),
    )

    assert duplicate.status_code == 409


def test_attendance_requires_authentication(
    attendance_api_environment,
):
    client, class_id, _ = attendance_api_environment

    response = client.post(
        "/api/attendance-sessions/",
        json=payload(class_id),
    )

    assert response.status_code == 401


def test_student_cannot_create_attendance(
    attendance_api_environment,
):
    client, class_id, _ = attendance_api_environment

    headers = login(
        client,
        "attendance_student",
        "StudentTestPassword123",
    )

    response = client.post(
        "/api/attendance-sessions/",
        headers=headers,
        json=payload(class_id),
    )

    assert response.status_code == 403


def test_unassigned_teacher_cannot_create_attendance(
    attendance_api_environment,
):
    client, class_id, _ = attendance_api_environment

    headers = login(
        client,
        "unassigned_teacher",
        "TeacherTestPassword123",
    )

    response = client.post(
        "/api/attendance-sessions/",
        headers=headers,
        json=payload(class_id),
    )

    assert response.status_code == 403


def test_future_attendance_date_rejected(
    attendance_api_environment,
):
    client, class_id, _ = attendance_api_environment

    headers = login(
        client,
        "attendance_teacher",
        "TeacherTestPassword123",
    )

    response = client.post(
        "/api/attendance-sessions/",
        headers=headers,
        json=payload(
            class_id,
            date.today() + timedelta(days=1),
        ),
    )

    assert response.status_code == 422
