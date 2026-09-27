
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.student import Student
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.attendance_record import AttendanceRecord
from backend.app.schemas.student_attendance_report import (
    StudentAttendanceReportResponse,
)


class StudentAttendanceReportNotFoundError(ValueError):
    pass


class StudentAcademicClassNotAssignedError(ValueError):
    pass


def get_student_attendance_report(
    db: Session,
    student_id: int,
) -> StudentAttendanceReportResponse:

    student = db.get(Student, student_id)

    if student is None:
        raise StudentAttendanceReportNotFoundError(
            "Student not found."
        )

    if student.academic_class_id is None:
        raise StudentAcademicClassNotAssignedError(
            "Student has no assigned academic class."
        )

    total_sessions = db.scalar(
        select(func.count(AttendanceSession.id)).where(
            AttendanceSession.academic_class_id
            == student.academic_class_id
        )
    ) or 0

    status_counts = dict(
        db.execute(
            select(
                AttendanceRecord.status,
                func.count(AttendanceRecord.id),
            )
            .join(
                AttendanceSession,
                AttendanceRecord.session_id
                == AttendanceSession.id,
            )
            .where(
                AttendanceRecord.student_id == student_id,
                AttendanceSession.academic_class_id
                == student.academic_class_id,
            )
            .group_by(AttendanceRecord.status)
        ).all()
    )

    present = status_counts.get("PRESENT", 0)
    absent = status_counts.get("ABSENT", 0)
    od = status_counts.get("OD", 0)
    late = status_counts.get("LATE", 0)

    marked_sessions = present + absent + od + late
    unmarked = max(total_sessions - marked_sessions, 0)

    attendance_percentage = (
        round(
            ((present + late) / total_sessions) * 100,
            2,
        )
        if total_sessions > 0
        else 0.0
    )

    return StudentAttendanceReportResponse(
        student_id=student_id,
        total_sessions=total_sessions,
        present=present,
        absent=absent,
        od=od,
        late=late,
        unmarked=unmarked,
        attendance_percentage=attendance_percentage,
    )
