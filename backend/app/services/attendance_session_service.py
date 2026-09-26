
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.academic_class import AcademicClass
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.teacher_assignment import TeacherAssignment
from backend.app.models.user import User
from backend.app.schemas.attendance_session import AttendanceSessionCreate


class InvalidAttendanceTeacherError(ValueError):
    pass


class AttendanceClassNotFoundError(ValueError):
    pass


class TeacherNotAssignedError(ValueError):
    pass


class InvalidAttendanceDateError(ValueError):
    pass


class DuplicateAttendanceSessionError(ValueError):
    pass


def create_attendance_session(
    db: Session,
    session_data: AttendanceSessionCreate,
    teacher_id: int,
) -> AttendanceSession:

    teacher = db.get(User, teacher_id)

    if (
        teacher is None
        or teacher.role != "TEACHER"
        or not teacher.is_active
    ):
        raise InvalidAttendanceTeacherError(
            "An active teacher account is required."
        )

    academic_class = db.get(
        AcademicClass,
        session_data.academic_class_id,
    )

    if academic_class is None:
        raise AttendanceClassNotFoundError(
            "Academic class not found."
        )

    assignment = db.scalar(
        select(TeacherAssignment).where(
            TeacherAssignment.teacher_id == teacher_id,
            TeacherAssignment.academic_class_id
            == session_data.academic_class_id,
        )
    )

    if assignment is None:
        raise TeacherNotAssignedError(
            "Teacher is not assigned to this class."
        )

    if session_data.attendance_date > date.today():
        raise InvalidAttendanceDateError(
            "Attendance cannot be created for a future date."
        )

    existing_session = db.scalar(
        select(AttendanceSession).where(
            AttendanceSession.academic_class_id
            == session_data.academic_class_id,
            AttendanceSession.attendance_date
            == session_data.attendance_date,
            AttendanceSession.period_number
            == session_data.period_number,
        )
    )

    if existing_session is not None:
        raise DuplicateAttendanceSessionError(
            "Attendance already exists for this class, date and period."
        )

    attendance_session = AttendanceSession(
        academic_class_id=session_data.academic_class_id,
        teacher_id=teacher_id,
        attendance_date=session_data.attendance_date,
        period_number=session_data.period_number,
        status="OPEN",
    )

    try:
        db.add(attendance_session)
        db.commit()
        db.refresh(attendance_session)

    except IntegrityError as exc:
        db.rollback()
        raise DuplicateAttendanceSessionError(
            "Attendance session could not be created. "
            "Check whether the class, date and period already exist."
        ) from exc

    except Exception:
        db.rollback()
        raise

    return attendance_session


class AttendanceSessionPermissionError(ValueError):
    pass


class AttendanceSessionAlreadyClosedError(ValueError):
    pass


class AttendanceSessionNotFoundForClosingError(ValueError):
    pass


def close_attendance_session(
    db: Session,
    session_id: int,
    teacher_id: int,
) -> AttendanceSession:
    attendance_session = db.get(
        AttendanceSession,
        session_id,
    )

    if attendance_session is None:
        raise AttendanceSessionNotFoundForClosingError(
            "Attendance session not found."
        )

    if attendance_session.teacher_id != teacher_id:
        raise AttendanceSessionPermissionError(
            "Only the session teacher can close attendance."
        )

    if attendance_session.status != "OPEN":
        raise AttendanceSessionAlreadyClosedError(
            "Attendance session is already closed."
        )

    attendance_session.status = "CLOSED"

    try:
        db.commit()
        db.refresh(attendance_session)
    except Exception:
        db.rollback()
        raise

    return attendance_session
