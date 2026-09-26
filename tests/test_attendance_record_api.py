
from datetime import date

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
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.department import Department
from backend.app.models.student import Student
from backend.app.models.user import User


@pytest.fixture
def attendance_record_api_environment():
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
            login_id="record_teacher",
            full_name="Record Teacher",
            password_hash=hash_password("TeacherTestPassword123"),
            role="TEACHER",
            is_active=True,
            must_change_password=False,
        )

        other_teacher = User(
            login_id="record_other_teacher",
            full_name="Other Teacher",
            password_hash=hash_password("TeacherTestPassword123"),
            role="TEACHER",
            is_active=True,
            must_change_password=False,
        )

        student_user = User(
            login_id="record_student",
            full_name="Record Student",
            password_hash=hash_password("StudentTestPassword123"),
            role="STUDENT",
            is_active=True,
            must_change_password=False,
        )

        db.add_all([teacher, other_teacher, student_user])
        db.flush()

        student = Student(
            user_id=student_user.id,
            academic_class_id=academic_class.id,
            college_id="API_TEST001",
            registration_number="API_REG001",
            department="Information Technology",
            class_name="IT-A",
            semester=5,
        )
        db.add(student)
        db.flush()

        attendance_session = AttendanceSession(
            academic_class_id=academic_class.id,
            teacher_id=teacher.id,
            attendance_date=date.today(),
            period_number=1,
            status="OPEN",
        )
        db.add(attendance_session)
        db.flush()

        session_id = attendance_session.id
        student_id = student.id

        db.commit()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client, session_id, student_id
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


def payload(session_id, student_id, status="PRESENT"):
    return {
        "session_id": session_id,
        "student_id": student_id,
        "status": status,
    }


def test_teacher_marks_attendance(
    attendance_record_api_environment,
):
    client, session_id, student_id = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    response = client.post(
        "/api/attendance-records/manual",
        headers=headers,
        json=payload(session_id, student_id),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "PRESENT"
    assert response.json()["marked_by"] == "MANUAL"


def test_duplicate_attendance_rejected(
    attendance_record_api_environment,
):
    client, session_id, student_id = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    first = client.post(
        "/api/attendance-records/manual",
        headers=headers,
        json=payload(session_id, student_id),
    )

    assert first.status_code == 201

    duplicate = client.post(
        "/api/attendance-records/manual",
        headers=headers,
        json=payload(session_id, student_id),
    )

    assert duplicate.status_code == 409


def test_attendance_requires_authentication(
    attendance_record_api_environment,
):
    client, session_id, student_id = (
        attendance_record_api_environment
    )

    response = client.post(
        "/api/attendance-records/manual",
        json=payload(session_id, student_id),
    )

    assert response.status_code == 401


def test_student_cannot_mark_attendance(
    attendance_record_api_environment,
):
    client, session_id, student_id = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_student",
        "StudentTestPassword123",
    )

    response = client.post(
        "/api/attendance-records/manual",
        headers=headers,
        json=payload(session_id, student_id),
    )

    assert response.status_code == 403


def test_other_teacher_cannot_mark_attendance(
    attendance_record_api_environment,
):
    client, session_id, student_id = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_other_teacher",
        "TeacherTestPassword123",
    )

    response = client.post(
        "/api/attendance-records/manual",
        headers=headers,
        json=payload(session_id, student_id),
    )

    assert response.status_code == 403


def test_missing_student_rejected(
    attendance_record_api_environment,
):
    client, session_id, _ = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    response = client.post(
        "/api/attendance-records/manual",
        headers=headers,
        json=payload(session_id, 99999),
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "attendance_status",
    ["PRESENT", "ABSENT", "OD", "LATE"],
)
def test_supported_attendance_statuses(
    attendance_record_api_environment,
    attendance_status,
):
    client, session_id, student_id = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    response = client.post(
        "/api/attendance-records/manual",
        headers=headers,
        json=payload(
            session_id,
            student_id,
            attendance_status,
        ),
    )

    assert response.status_code == 201
    assert response.json()["status"] == attendance_status


def test_teacher_retrieves_own_attendance(
    attendance_record_api_environment,
):
    client, session_id, student_id = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    create_response = client.post(
        "/api/attendance-records/manual",
        headers=headers,
        json=payload(session_id, student_id),
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/api/attendance-records/session/{session_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["student_id"] == student_id
    assert response.json()[0]["status"] == "PRESENT"


def test_other_teacher_cannot_retrieve_attendance(
    attendance_record_api_environment,
):
    client, session_id, _ = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_other_teacher",
        "TeacherTestPassword123",
    )

    response = client.get(
        f"/api/attendance-records/session/{session_id}",
        headers=headers,
    )

    assert response.status_code == 403


def test_student_cannot_retrieve_attendance(
    attendance_record_api_environment,
):
    client, session_id, _ = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_student",
        "StudentTestPassword123",
    )

    response = client.get(
        f"/api/attendance-records/session/{session_id}",
        headers=headers,
    )

    assert response.status_code == 403


def test_retrieval_requires_authentication(
    attendance_record_api_environment,
):
    client, session_id, _ = (
        attendance_record_api_environment
    )

    response = client.get(
        f"/api/attendance-records/session/{session_id}",
    )

    assert response.status_code == 401


def test_retrieval_rejects_missing_session(
    attendance_record_api_environment,
):
    client, _, _ = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    response = client.get(
        "/api/attendance-records/session/99999",
        headers=headers,
    )

    assert response.status_code == 404


def test_teacher_retrieves_empty_session(
    attendance_record_api_environment,
):
    client, session_id, _ = (
        attendance_record_api_environment
    )

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    response = client.get(
        f"/api/attendance-records/session/{session_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []
