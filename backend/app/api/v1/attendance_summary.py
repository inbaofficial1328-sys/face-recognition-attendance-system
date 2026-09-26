
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_db, require_roles
from backend.app.schemas.attendance_summary import AttendanceSummaryResponse
from backend.app.services.attendance_summary_service import (
    AttendanceSummaryNotFoundError,
    AttendanceSummaryPermissionError,
    get_attendance_summary,
)


router = APIRouter(
    prefix="/api/attendance-sessions",
    tags=["Attendance Summary"],
)


@router.get(
    "/{session_id}/summary",
    response_model=AttendanceSummaryResponse,
)
def retrieve_attendance_summary(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("TEACHER")),
):
    try:
        return get_attendance_summary(
            db=db,
            session_id=session_id,
            teacher_id=current_user.id,
        )

    except AttendanceSummaryNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except AttendanceSummaryPermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc
