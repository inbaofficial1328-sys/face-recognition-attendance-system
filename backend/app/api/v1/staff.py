
import os

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session
from fastapi import Body
from backend.app.core.dependencies import (
    get_db,
    require_roles,
)
from backend.app.schemas.staff import (
    StaffCreate,
    StaffRegistrationResponse,
    StaffResponse,
    StaffStatusUpdate,
)
from backend.app.services.staff_service import (
    DuplicateStaffError,
    get_staff_accounts,
    register_staff,
    set_staff_active_status,
)

router = APIRouter(
    prefix="/api/staff",
    tags=["Staff Management"],
)


@router.post(
    "/",
    response_model=StaffRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_staff_account(
    staff_data: StaffCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    # Keep registration disabled unless explicitly enabled.
    if os.getenv("ENABLE_STAFF_REGISTRATION") != "true":
        raise HTTPException(
            status_code=503,
            detail="Staff registration is not enabled.",
        )

    # The response contains a temporary credential.
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"

    try:
        staff, temporary_password = register_staff(
            db,
            staff_data,
        )

    except DuplicateStaffError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return StaffRegistrationResponse(
        staff=StaffResponse.model_validate(staff),
        temporary_password=temporary_password,
    )

@router.get(
    "/",
    response_model=list[StaffResponse],
)
def list_staff_accounts(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return get_staff_accounts(db)

@router.patch(
    "/{staff_id}/status",
    response_model=StaffResponse,
)
def update_staff_status(
    staff_id: int,
    status_data: StaffStatusUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    try:
        return set_staff_active_status(
            db=db,
            staff_id=staff_id,
            is_active=status_data.is_active,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
