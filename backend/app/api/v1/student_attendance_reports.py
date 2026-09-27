
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_db,
    require_roles,
)
from backend.app.models.student import Student
from backend.app.models.user import User
from backend.app.schemas.student_attendance_report import (
    StudentAttendanceReportResponse,
)
from backend.app.services.student_attendance_report_service import (
    StudentAcademicClassNotAssignedError,
    StudentAttendanceReportNotFoundError,
    get_student_attendance_report,
)
from backend.app.models.teacher_assignment import TeacherAssignment

router = APIRouter(
    prefix="/api/student-attendance-reports",
    tags=["Student Attendance Reports"],
)


@router.get(
    "/me",
    response_model=StudentAttendanceReportResponse,
)
def get_my_attendance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STUDENT")),
):
    student = db.scalar(
        select(Student).where(
            Student.user_id == current_user.id
        )
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found.",
        )

    try:
        return get_student_attendance_report(
            db=db,
            student_id=student.id,
        )

    except StudentAttendanceReportNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except StudentAcademicClassNotAssignedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.get(
    "/students/{student_id}",
    response_model=StudentAttendanceReportResponse,
)
def get_student_report_for_teacher(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("TEACHER")),
):
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    assignment = db.scalar(
        select(TeacherAssignment).where(
            TeacherAssignment.teacher_id == current_user.id,
            TeacherAssignment.academic_class_id
            == student.academic_class_id,
        )
    )

    if assignment is None:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this student's class.",
        )

    try:
        return get_student_attendance_report(
            db=db,
            student_id=student_id,
        )

    except StudentAttendanceReportNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except StudentAcademicClassNotAssignedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
