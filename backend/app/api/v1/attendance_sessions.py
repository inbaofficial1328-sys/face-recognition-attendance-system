
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_db, require_roles
from backend.app.schemas.attendance_session import (
    AttendanceSessionCreate,
    AttendanceSessionResponse,
)
from backend.app.services.attendance_session_service import (
    AttendanceClassNotFoundError,
    DuplicateAttendanceSessionError,
    InvalidAttendanceDateError,
    InvalidAttendanceTeacherError,
    TeacherNotAssignedError,
    create_attendance_session,
)

from backend.app.services.attendance_session_service import (
    close_attendance_session,
    AttendanceSessionPermissionError,
    AttendanceSessionAlreadyClosedError,
    AttendanceSessionNotFoundForClosingError,
)

router = APIRouter(
    prefix="/api/attendance-sessions",
    tags=["Attendance Sessions"],
)


@router.post(
    "/",
    response_model=AttendanceSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    session_data: AttendanceSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("TEACHER")),
):
    try:
        return create_attendance_session(
            db=db,
            session_data=session_data,
            teacher_id=current_user.id,
        )

    except AttendanceClassNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except InvalidAttendanceTeacherError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except TeacherNotAssignedError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except InvalidAttendanceDateError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except DuplicateAttendanceSessionError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{session_id}/close",
    response_model=AttendanceSessionResponse,
)
def close_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("TEACHER")),
):
    try:
        return close_attendance_session(
            db=db,
            session_id=session_id,
            teacher_id=current_user.id,
        )

    except AttendanceSessionNotFoundForClosingError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except AttendanceSessionPermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except AttendanceSessionAlreadyClosedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
