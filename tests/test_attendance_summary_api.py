
from tests.test_attendance_correction_api import (
    correction_api_environment,
    login,
)


def summary_url(session_id):
    return f"/api/attendance-sessions/{session_id}/summary"


def test_teacher_retrieves_attendance_summary(
    correction_api_environment,
):
    client, _, _, session_id = correction_api_environment

    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.get(
        summary_url(session_id),
        headers=headers,
    )

    assert response.status_code == 200

    summary = response.json()

    assert summary["session_id"] == session_id
    assert summary["total_students"] == 1
    assert summary["present"] == 0
    assert summary["absent"] == 1
    assert summary["od"] == 0
    assert summary["late"] == 0
    assert summary["unmarked"] == 0
    assert summary["attendance_percentage"] == 0.0


def test_attendance_summary_requires_authentication(
    correction_api_environment,
):
    client, _, _, session_id = correction_api_environment

    response = client.get(
        summary_url(session_id),
    )

    assert response.status_code == 401


def test_student_cannot_view_attendance_summary(
    correction_api_environment,
):
    client, _, _, session_id = correction_api_environment

    headers = login(
        client,
        "correction_api_student",
        "StudentTestPassword123",
    )

    response = client.get(
        summary_url(session_id),
        headers=headers,
    )

    assert response.status_code == 403


def test_other_teacher_cannot_view_attendance_summary(
    correction_api_environment,
):
    client, _, _, session_id = correction_api_environment

    headers = login(
        client,
        "correction_api_other",
        "TeacherTestPassword123",
    )

    response = client.get(
        summary_url(session_id),
        headers=headers,
    )

    assert response.status_code == 403


def test_attendance_summary_session_not_found(
    correction_api_environment,
):
    client, _, _, _ = correction_api_environment

    headers = login(
        client,
        "correction_api_teacher",
        "TeacherTestPassword123",
    )

    response = client.get(
        summary_url(999999),
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Attendance session not found."
    )
