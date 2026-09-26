
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.attendance_record import AttendanceRecord
from backend.app.models.student import Student
from backend.app.schemas.attendance_summary import AttendanceSummaryResponse


class AttendanceSummaryNotFoundError(ValueError):
    pass


class AttendanceSummaryPermissionError(ValueError):
    pass


def get_attendance_summary(
    db: Session,
    session_id: int,
    teacher_id: int,
) -> AttendanceSummaryResponse:

    attendance_session = db.get(AttendanceSession, session_id)

    if attendance_session is None:
        raise AttendanceSummaryNotFoundError(
            "Attendance session not found."
        )

    if attendance_session.teacher_id != teacher_id:
        raise AttendanceSummaryPermissionError(
            "Only the session teacher can view this summary."
        )

    total_students = db.scalar(
        select(func.count(Student.id)).where(
            Student.academic_class_id
            == attendance_session.academic_class_id
        )
    ) or 0

    status_counts = dict(
        db.execute(
            select(
                AttendanceRecord.status,
                func.count(AttendanceRecord.id),
            )
            .where(AttendanceRecord.session_id == session_id)
            .group_by(AttendanceRecord.status)
        ).all()
    )

    present = status_counts.get("PRESENT", 0)
    absent = status_counts.get("ABSENT", 0)
    od = status_counts.get("OD", 0)
    late = status_counts.get("LATE", 0)

    marked_students = present + absent + od + late

    unmarked = max(total_students - marked_students, 0)

    attendance_percentage = (
        round(((present + late) / total_students) * 100, 2)
        if total_students > 0
        else 0.0
    )

    return AttendanceSummaryResponse(
        session_id=session_id,
        total_students=total_students,
        present=present,
        absent=absent,
        od=od,
        late=late,
        unmarked=unmarked,
        attendance_percentage=attendance_percentage,
    )
