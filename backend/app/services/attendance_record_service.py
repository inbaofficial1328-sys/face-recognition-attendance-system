
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.attendance_record import AttendanceRecord
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.student import Student
from backend.app.schemas.attendance_record import AttendanceRecordCreate


class AttendanceSessionNotFoundError(ValueError):
    pass


class AttendancePermissionError(ValueError):
    pass


class AttendanceSessionClosedError(ValueError):
    pass


class AttendanceStudentNotFoundError(ValueError):
    pass


class AttendanceClassMismatchError(ValueError):
    pass


class DuplicateAttendanceRecordError(ValueError):
    pass


def mark_manual_attendance(
    db: Session,
    record_data: AttendanceRecordCreate,
    teacher_id: int,
) -> AttendanceRecord:

    attendance_session = db.get(
        AttendanceSession,
        record_data.session_id,
    )

    if attendance_session is None:
        raise AttendanceSessionNotFoundError(
            "Attendance session not found."
        )

    if attendance_session.teacher_id != teacher_id:
        raise AttendancePermissionError(
            "Only the session teacher can mark attendance."
        )

    if attendance_session.status != "OPEN":
        raise AttendanceSessionClosedError(
            "Attendance session is closed."
        )

    student = db.get(
        Student,
        record_data.student_id,
    )

    if student is None:
        raise AttendanceStudentNotFoundError(
            "Student not found."
        )

    if (
        student.academic_class_id
        != attendance_session.academic_class_id
    ):
        raise AttendanceClassMismatchError(
            "Student does not belong to this academic class."
        )

    existing_record = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id
            == record_data.session_id,
            AttendanceRecord.student_id
            == record_data.student_id,
        )
    )

    if existing_record is not None:
        raise DuplicateAttendanceRecordError(
            "Attendance has already been marked for this student."
        )

    record = AttendanceRecord(
        session_id=record_data.session_id,
        student_id=record_data.student_id,
        status=record_data.status,
        marked_by="MANUAL",
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)

    except IntegrityError as exc:
        db.rollback()
        raise DuplicateAttendanceRecordError(
            "Attendance could not be saved. "
            "Check whether a record already exists."
        ) from exc

    except Exception:
        db.rollback()
        raise

    return record


def get_session_attendance_records(
    db: Session,
    session_id: int,
    teacher_id: int,
) -> list[AttendanceRecord]:
    attendance_session = db.get(
        AttendanceSession,
        session_id,
    )

    if attendance_session is None:
        raise AttendanceSessionNotFoundError(
            "Attendance session not found."
        )

    if attendance_session.teacher_id != teacher_id:
        raise AttendancePermissionError(
            "Only the session teacher can view attendance."
        )

    records = db.scalars(
        select(AttendanceRecord)
        .where(AttendanceRecord.session_id == session_id)
        .order_by(AttendanceRecord.student_id)
    ).all()

    return list(records)
