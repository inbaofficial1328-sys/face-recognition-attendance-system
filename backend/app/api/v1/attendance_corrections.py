
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_db, require_roles
from backend.app.schemas.attendance_correction import (
    AttendanceCorrectionRequest,
)
from backend.app.schemas.attendance_record import (
    AttendanceRecordResponse,
)
from backend.app.services.attendance_correction_service import (
    CorrectionPermissionError,
    CorrectionRecordNotFoundError,
    CorrectionSessionClosedError,
    CorrectionUnchangedStatusError,
    correct_attendance,
)


router = APIRouter(
    prefix="/api/attendance-records",
    tags=["Attendance Corrections"],
)


@router.patch(
    "/{record_id}/correct",
    response_model=AttendanceRecordResponse,
    status_code=status.HTTP_200_OK,
)
def correct_attendance_record(
    record_id: int,
    correction_data: AttendanceCorrectionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("TEACHER")),
):
    try:
        return correct_attendance(
            db=db,
            record_id=record_id,
            correction_data=correction_data,
            teacher_id=current_user.id,
        )

    except CorrectionRecordNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except CorrectionPermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except (
        CorrectionSessionClosedError,
        CorrectionUnchangedStatusError,
    ) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
