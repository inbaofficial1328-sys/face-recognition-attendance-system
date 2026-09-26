
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from backend.app.schemas.attendance_session import AttendanceSessionCreate
from backend.app.services.attendance_session_service import (
    AttendanceClassNotFoundError,
    DuplicateAttendanceSessionError,
    InvalidAttendanceDateError,
    InvalidAttendanceTeacherError,
    TeacherNotAssignedError,
    create_attendance_session,
)


def request(attendance_date=None):
    return AttendanceSessionCreate(
        academic_class_id=1,
        attendance_date=attendance_date or date.today(),
        period_number=2,
    )


def configured_db():
    db = MagicMock()

    teacher = MagicMock()
    teacher.role = "TEACHER"
    teacher.is_active = True

    db.get.side_effect = [teacher, MagicMock()]
    db.scalar.side_effect = [MagicMock(), None]

    return db


def test_assigned_teacher_creates_session():
    db = configured_db()

    result = create_attendance_session(
        db,
        request(),
        5,
    )

    assert result.academic_class_id == 1
    assert result.teacher_id == 5
    assert result.attendance_date == date.today()
    assert result.period_number == 2
    assert result.status == "OPEN"

    db.add.assert_called_once_with(result)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)


def test_rejects_invalid_teacher():
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(InvalidAttendanceTeacherError):
        create_attendance_session(db, request(), 5)

    db.commit.assert_not_called()


def test_rejects_missing_class():
    db = MagicMock()

    teacher = MagicMock()
    teacher.role = "TEACHER"
    teacher.is_active = True

    db.get.side_effect = [teacher, None]

    with pytest.raises(AttendanceClassNotFoundError):
        create_attendance_session(db, request(), 5)


def test_rejects_unassigned_teacher():
    db = configured_db()

    db.scalar.side_effect = [None]

    with pytest.raises(TeacherNotAssignedError):
        create_attendance_session(
            db,
            request(),
            5,
        )

    db.commit.assert_not_called()


def test_rejects_future_date():
    db = configured_db()

    future_request = request(
        date.today() + timedelta(days=1)
    )

    with pytest.raises(InvalidAttendanceDateError):
        create_attendance_session(db, future_request, 5)


def test_rejects_duplicate_session():
    db = configured_db()
    db.scalar.side_effect = [MagicMock(), MagicMock()]

    with pytest.raises(DuplicateAttendanceSessionError):
        create_attendance_session(db, request(), 5)

    db.commit.assert_not_called()
