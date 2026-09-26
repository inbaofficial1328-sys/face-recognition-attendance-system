
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_db, require_roles
from backend.app.schemas.attendance_record import (
    AttendanceRecordCreate,
    AttendanceRecordResponse,
)
from backend.app.services.attendance_record_service import (
    AttendanceClassMismatchError,
    AttendancePermissionError,
    AttendanceSessionClosedError,
    AttendanceSessionNotFoundError,
    AttendanceStudentNotFoundError,
    DuplicateAttendanceRecordError,
    mark_manual_attendance,
)

from backend.app.services.attendance_record_service import (
    get_session_attendance_records,
)

router = APIRouter(
    prefix="/api/attendance-records",
    tags=["Attendance Records"],
)


@router.post(
    "/manual",
    response_model=AttendanceRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_manual_attendance(
    record_data: AttendanceRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("TEACHER")),
):
    try:
        return mark_manual_attendance(
            db=db,
            record_data=record_data,
            teacher_id=current_user.id,
        )

    except (
        AttendanceSessionNotFoundError,
        AttendanceStudentNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except AttendancePermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except AttendanceClassMismatchError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except (
        AttendanceSessionClosedError,
        DuplicateAttendanceRecordError,
    ) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.get(
    "/session/{session_id}",
    response_model=list[AttendanceRecordResponse],
)
def retrieve_session_attendance(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("TEACHER")),
):
    try:
        return get_session_attendance_records(
            db=db,
            session_id=session_id,
            teacher_id=current_user.id,
        )

    except AttendanceSessionNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except AttendancePermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc
