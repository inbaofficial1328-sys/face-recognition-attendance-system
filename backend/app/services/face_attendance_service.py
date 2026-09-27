"""Fail-closed bridge from a validated face identity to attendance.

This module does not perform face recognition. It only accepts a server-side
VerifiedFaceIdentity produced by an independently validated recognition
pipeline. Candidate/review results cannot mark attendance.
"""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.attendance_record import AttendanceRecord
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.student import Student


class FaceAttendanceSessionError(ValueError):
    pass


class FaceAttendanceDuplicateError(ValueError):
    pass


class FaceAttendanceClassMismatchError(ValueError):
    pass


@dataclass(frozen=True)
class VerifiedFaceIdentity:
    student_id: int
    verified: bool
    verification_source: str

    def __post_init__(self):
        if type(self.student_id) is not int or self.student_id <= 0:
            raise ValueError("Invalid student ID.")
        if self.verification_source != "validated_face_pipeline":
            raise ValueError("Untrusted face verification source.")
        if self.verified is not True:
            raise ValueError("Face identity is not verified.")


def mark_verified_face_attendance(
    db: Session,
    session_id: int,
    identity: VerifiedFaceIdentity,
) -> AttendanceRecord:
    """Mark PRESENT attendance only for an independently verified identity."""
    attendance_session = db.get(AttendanceSession, session_id)
    if attendance_session is None:
        raise FaceAttendanceSessionError("Attendance session not found.")

    if attendance_session.status != "OPEN":
        raise FaceAttendanceSessionError("Attendance session is closed.")

    student = db.get(Student, identity.student_id)
    if student is None:
        raise FaceAttendanceClassMismatchError("Student not found.")

    if student.academic_class_id != attendance_session.academic_class_id:
        raise FaceAttendanceClassMismatchError(
            "Student does not belong to this academic class."
        )

    existing = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id == session_id,
            AttendanceRecord.student_id == identity.student_id,
        )
    )
    if existing is not None:
        raise FaceAttendanceDuplicateError(
            "Attendance has already been marked for this student."
        )

    record = AttendanceRecord(
        session_id=session_id,
        student_id=identity.student_id,
        status="PRESENT",
        marked_by="FACE_RECOGNITION",
        marked_at=datetime.now(timezone.utc),
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except IntegrityError as exc:
        db.rollback()
        raise FaceAttendanceDuplicateError(
            "Attendance could not be saved because a record already exists."
        ) from exc
    except Exception:
        db.rollback()
        raise

    return record
