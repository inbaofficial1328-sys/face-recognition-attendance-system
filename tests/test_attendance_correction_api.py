
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.dependencies import get_db
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.models.academic_class import AcademicClass
from backend.app.models.attendance_correction import AttendanceCorrection
from backend.app.models.attendance_record import AttendanceRecord
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.department import Department
from backend.app.models.student import Student
from backend.app.models.user import User


@pytest.fixture
def correction_api_environment():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
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

            users = [
                User(
                    login_id="correction_api_teacher",
                    full_name="Correction Teacher",
                    password_hash=hash_password(
                        "TeacherTestPassword123"
                    ),
                    role="TEACHER",
                    is_active=True,
                    must_change_password=False,
                ),
                User(
                    login_id="correction_api_other",
                    full_name="Other Teacher",
                    password_hash=hash_password(
                        "TeacherTestPassword123"
                    ),
                    role="TEACHER",
                    is_active=True,
                    must_change_password=False,
                ),
                User(
                    login_id="correction_api_student",
                    full_name="Student",
                    password_hash=hash_password(
                        "StudentTestPassword123"
                    ),
                    role="STUDENT",
                    is_active=True,
                    must_change_password=False,
                ),
            ]

            db.add_all(users)
            db.flush()

            student = Student(
                user_id=users[2].id,
                academic_class_id=academic_class.id,
                college_id="CORR_API001",
                registration_number="CORR_API_REG001",
                department="Information Technology",
                class_name="IT-A",
                semester=5,
            )
            db.add(student)
            db.flush()

            attendance_session = AttendanceSession(
                academic_class_id=academic_class.id,
                teacher_id=users[0].id,
                attendance_date=datetime.now(
                    timezone.utc
                ).date(),
                period_number=1,
                status="OPEN",
            )
            db.add(attendance_session)
            db.flush()

            record = AttendanceRecord(
                session_id=attendance_session.id,
                student_id=student.id,
                status="ABSENT",
                marked_by="FACE_RECOGNITION",
                marked_at=datetime(
                    2026, 9, 1, 9, 0,
                    tzinfo=timezone.utc,
                ),
            )
            db.add(record)
            db.commit()

            record_id = record.id
            session_id = attendance_session.id

        def override_get_db():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as client:
            yield client, engine, record_id, session_id

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


def correction_payload(status="PRESENT"):
    return {
        "status": status,
        "reason": "Verified by the class teacher",
    }


def correction_url(record_id):
    return f"/api/attendance-records/{record_id}/correct"


def test_teacher_corrects_attendance_and_creates_audit(
    correction_api_environment,
):
    client, engine, record_id, _ = correction_api_environment
    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.patch(
        correction_url(record_id),
        headers=headers,
        json=correction_payload(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PRESENT"
    assert response.json()["marked_by"] == "FACE_RECOGNITION"

    with Session(engine) as db:
        entries = db.scalars(
            select(AttendanceCorrection)
        ).all()

        assert len(entries) == 1
        assert entries[0].old_status == "ABSENT"
        assert entries[0].new_status == "PRESENT"
        assert entries[0].reason == (
            "Verified by the class teacher"
        )


def test_unauthenticated_correction_is_rejected(
    correction_api_environment,
):
    client, _, record_id, _ = correction_api_environment

    response = client.patch(
        correction_url(record_id),
        json=correction_payload(),
    )

    assert response.status_code == 401


def test_student_cannot_correct_attendance(
    correction_api_environment,
):
    client, _, record_id, _ = correction_api_environment
    headers = login(
        client,
        "correction_api_student",
        "StudentTestPassword123",
    )

    response = client.patch(
        correction_url(record_id),
        headers=headers,
        json=correction_payload(),
    )

    assert response.status_code == 403


def test_other_teacher_cannot_correct_attendance(
    correction_api_environment,
):
    client, _, record_id, _ = correction_api_environment
    headers = login(
        client,
        "correction_api_other",
        "TeacherTestPassword123",
    )

    response = client.patch(
        correction_url(record_id),
        headers=headers,
        json=correction_payload(),
    )

    assert response.status_code == 403


def test_missing_record_returns_404(
    correction_api_environment,
):
    client, _, _, _ = correction_api_environment
    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.patch(
        correction_url(999999),
        headers=headers,
        json=correction_payload(),
    )

    assert response.status_code == 404


def test_closed_session_returns_409(
    correction_api_environment,
):
    client, engine, record_id, session_id = (
        correction_api_environment
    )

    with Session(engine) as db:
        attendance_session = db.get(
            AttendanceSession,
            session_id,
        )
        attendance_session.status = "CLOSED"
        db.commit()

    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.patch(
        correction_url(record_id),
        headers=headers,
        json=correction_payload(),
    )

    assert response.status_code == 409


def test_unchanged_status_returns_409(
    correction_api_environment,
):
    client, _, record_id, _ = correction_api_environment
    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.patch(
        correction_url(record_id),
        headers=headers,
        json=correction_payload("ABSENT"),
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "INVALID", "reason": "Valid reason"},
        {"status": "PRESENT", "reason": "No"},
        {"status": "PRESENT", "reason": "   "},
        {
            "status": "PRESENT",
            "reason": "Valid reason",
            "unexpected": True,
        },
    ],
)
def test_invalid_payload_returns_422(
    correction_api_environment,
    payload,
):
    client, _, record_id, _ = correction_api_environment
    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.patch(
        correction_url(record_id),
        headers=headers,
        json=payload,
    )

    assert response.status_code == 422


def history_url(record_id):
    return f"/api/attendance-records/{record_id}/corrections"


def test_teacher_retrieves_chronological_history(
    correction_api_environment,
):
    client, _, record_id, _ = correction_api_environment

    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    for attendance_status in ["PRESENT", "OD"]:
        response = client.patch(
            correction_url(record_id),
            headers=headers,
            json=correction_payload(attendance_status),
        )
        assert response.status_code == 200

    response = client.get(
        history_url(record_id),
        headers=headers,
    )

    assert response.status_code == 200

    history = response.json()
    assert len(history) == 2

    assert history[0]["old_status"] == "ABSENT"
    assert history[0]["new_status"] == "PRESENT"
    assert history[1]["old_status"] == "PRESENT"
    assert history[1]["new_status"] == "OD"

    assert history[0]["id"] < history[1]["id"]


def test_uncorrected_record_returns_empty_history(
    correction_api_environment,
):
    client, _, record_id, _ = correction_api_environment

    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.get(
        history_url(record_id),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_history_requires_authentication(
    correction_api_environment,
):
    client, _, record_id, _ = correction_api_environment

    response = client.get(history_url(record_id))

    assert response.status_code == 401


def test_other_teacher_cannot_view_history(
    correction_api_environment,
):
    client, _, record_id, _ = correction_api_environment

    headers = login(
        client,
        "correction_api_other",
        "TeacherTestPassword123",
    )

    response = client.get(
        history_url(record_id),
        headers=headers,
    )

    assert response.status_code == 403


def test_missing_record_history_returns_404(
    correction_api_environment,
):
    client, _, _, _ = correction_api_environment

    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.get(
        history_url(999999),
        headers=headers,
    )

    assert response.status_code == 404
