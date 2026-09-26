from sqlalchemy.orm import Session

from backend.app.models.attendance_correction import AttendanceCorrection
from backend.app.models.attendance_record import AttendanceRecord
from backend.app.models.attendance_session import AttendanceSession
from backend.app.schemas.attendance_correction import (
    AttendanceCorrectionRequest,
)
from sqlalchemy import select


class CorrectionRecordNotFoundError(ValueError):
    pass


class CorrectionPermissionError(ValueError):
    pass


class CorrectionSessionClosedError(ValueError):
    pass


class CorrectionUnchangedStatusError(ValueError):
    pass


def correct_attendance(
    db: Session,
    record_id: int,
    correction_data: AttendanceCorrectionRequest,
    teacher_id: int,
) -> AttendanceRecord:

    record = db.get(AttendanceRecord, record_id)

    if record is None:
        raise CorrectionRecordNotFoundError(
            "Attendance record not found."
        )

    attendance_session = db.get(
        AttendanceSession,
        record.session_id,
    )

    if attendance_session is None:
        raise CorrectionRecordNotFoundError(
            "Associated attendance session not found."
        )

    if attendance_session.teacher_id != teacher_id:
        raise CorrectionPermissionError(
            "Only the session teacher can correct attendance."
        )

    if attendance_session.status != "OPEN":
        raise CorrectionSessionClosedError(
            "Closed attendance sessions cannot be corrected."
        )

    if record.status == correction_data.status:
        raise CorrectionUnchangedStatusError(
            "The new status must differ from the existing status."
        )

    previous_status = record.status

    audit_entry = AttendanceCorrection(
        attendance_record_id=record.id,
        corrected_by=teacher_id,
        old_status=previous_status,
        new_status=correction_data.status,
        reason=correction_data.reason,
    )

    try:
        record.status = correction_data.status

        db.add(audit_entry)
        db.commit()
        db.refresh(record)

    except Exception:
        db.rollback()
        raise

    return record


def get_attendance_correction_history(
    db: Session,
    record_id: int,
    teacher_id: int,
) -> list[AttendanceCorrection]:

    record = db.get(
        AttendanceRecord,
        record_id,
    )

    if record is None:
        raise CorrectionRecordNotFoundError(
            "Attendance record not found."
        )

    attendance_session = db.get(
        AttendanceSession,
        record.session_id,
    )

    if attendance_session is None:
        raise CorrectionRecordNotFoundError(
            "Associated attendance session not found."
        )

    if attendance_session.teacher_id != teacher_id:
        raise CorrectionPermissionError(
            "Only the session teacher can view correction history."
        )

    statement = (
        select(AttendanceCorrection)
        .where(
            AttendanceCorrection.attendance_record_id == record_id
        )
        .order_by(
            AttendanceCorrection.corrected_at.asc(),
            AttendanceCorrection.id.asc(),
        )
    )

    return list(db.scalars(statement).all())
