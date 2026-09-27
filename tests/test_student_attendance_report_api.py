
from fastapi.testclient import TestClient

from backend.app.main import app
from tests.test_attendance_correction_api import (
    correction_api_environment,
    login,
)

def test_student_attendance_report_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/student-attendance-reports/me"
        )

    assert response.status_code == 401


def test_student_can_view_own_attendance_report(
    correction_api_environment,
):
    client, _, _, _ = correction_api_environment

    headers = login(
        client,
        "correction_api_student",
        "StudentTestPassword123",
    )

    response = client.get(
        "/api/student-attendance-reports/me",
        headers=headers,
    )

    assert response.status_code == 200

    report = response.json()

    assert report["total_sessions"] == 1
    assert report["present"] == 0
    assert report["absent"] == 1
    assert report["od"] == 0
    assert report["late"] == 0
    assert report["unmarked"] == 0
    assert report["attendance_percentage"] == 0.0


def test_teacher_cannot_access_student_self_report(
    correction_api_environment,
):
    client, _, _, _ = correction_api_environment

    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.get(
        "/api/student-attendance-reports/me",
        headers=headers,
    )

    assert response.status_code == 403


def test_unassigned_teacher_cannot_view_student_report(
    correction_api_environment,
):
    client, engine, _, _ = correction_api_environment

    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    # The existing test fixture has no teacher assignments.
    # Retrieve the test student's ID.
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from backend.app.models.student import Student

    with Session(engine) as db:
        student_id = db.scalar(
            select(Student.id)
        )

    response = client.get(
        f"/api/student-attendance-reports/students/{student_id}",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You are not assigned to this student's class."
    )


def test_assigned_teacher_can_view_student_report(
    correction_api_environment,
):
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from backend.app.models.student import Student
    from backend.app.models.teacher_assignment import TeacherAssignment
    from backend.app.models.user import User

    client, engine, _, _ = correction_api_environment

    with Session(engine) as db:
        student = db.scalars(select(Student)).one()

        teacher = db.scalars(
            select(User).where(
                User.login_id == "correction_api_teacher"
            )
        ).one()

        assignment = TeacherAssignment(
            teacher_id=teacher.id,
            academic_class_id=student.academic_class_id,
        )

        db.add(assignment)
        db.commit()

        student_id = student.id

    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.get(
        f"/api/student-attendance-reports/students/{student_id}",
        headers=headers,
    )

    assert response.status_code == 200

    report = response.json()

    assert report["student_id"] == student_id
    assert report["total_sessions"] == 1
    assert report["present"] == 0
    assert report["absent"] == 1
    assert report["attendance_percentage"] == 0.0


def test_student_cannot_access_teacher_report_endpoint(
    correction_api_environment,
):
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from backend.app.models.student import Student

    client, engine, _, _ = correction_api_environment

    with Session(engine) as db:
        student_id = db.scalar(select(Student.id))

    headers = login(
        client,
        "correction_api_student",
        "StudentTestPassword123",
    )

    response = client.get(
        f"/api/student-attendance-reports/students/{student_id}",
        headers=headers,
    )

    assert response.status_code == 403


def test_teacher_report_returns_404_for_missing_student(
    correction_api_environment,
):
    client, _, _, _ = correction_api_environment

    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.get(
        "/api/student-attendance-reports/students/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found."
