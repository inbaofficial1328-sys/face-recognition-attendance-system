
import pytest

from backend.app.models.attendance_session import AttendanceSession
from tests.test_attendance_record_api import (
    attendance_record_api_environment,
    login,
    payload,
)


@pytest.fixture
def closing_environment(attendance_record_api_environment):
    return attendance_record_api_environment


def test_teacher_closes_own_session(closing_environment):
    client, session_id, _ = closing_environment

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    response = client.patch(
        f"/api/attendance-sessions/{session_id}/close",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CLOSED"


def test_other_teacher_cannot_close_session(closing_environment):
    client, session_id, _ = closing_environment

    headers = login(
        client,
        "record_other_teacher",
        "TeacherTestPassword123",
    )

    response = client.patch(
        f"/api/attendance-sessions/{session_id}/close",
        headers=headers,
    )

    assert response.status_code == 403


def test_student_cannot_close_session(closing_environment):
    client, session_id, _ = closing_environment

    headers = login(
        client,
        "record_student",
        "StudentTestPassword123",
    )

    response = client.patch(
        f"/api/attendance-sessions/{session_id}/close",
        headers=headers,
    )

    assert response.status_code == 403


def test_closing_requires_authentication(closing_environment):
    client, session_id, _ = closing_environment

    response = client.patch(
        f"/api/attendance-sessions/{session_id}/close",
    )

    assert response.status_code == 401


def test_session_cannot_be_closed_twice(closing_environment):
    client, session_id, _ = closing_environment

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    first = client.patch(
        f"/api/attendance-sessions/{session_id}/close",
        headers=headers,
    )

    assert first.status_code == 200

    second = client.patch(
        f"/api/attendance-sessions/{session_id}/close",
        headers=headers,
    )

    assert second.status_code == 409


def test_missing_session_cannot_be_closed(closing_environment):
    client, _, _ = closing_environment

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    response = client.patch(
        "/api/attendance-sessions/99999/close",
        headers=headers,
    )

    assert response.status_code == 404


def test_closed_session_rejects_manual_attendance(
    closing_environment,
):
    client, session_id, student_id = closing_environment

    headers = login(
        client,
        "record_teacher",
        "TeacherTestPassword123",
    )

    close_response = client.patch(
        f"/api/attendance-sessions/{session_id}/close",
        headers=headers,
    )

    assert close_response.status_code == 200

    attendance_response = client.post(
        "/api/attendance-records/manual",
        headers=headers,
        json=payload(session_id, student_id),
    )

    assert attendance_response.status_code == 409
