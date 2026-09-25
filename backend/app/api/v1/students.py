import os

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_db, require_roles
from backend.app.schemas.student import (
    StudentCreate,
    StudentResponse,
    StudentRegistrationResponse,
)
from backend.app.services.student_service import (
    DuplicateStudentError,
    get_students,
    register_student,
)

router = APIRouter(
    prefix="/api/students",
    tags=["Students"],
)

@router.post(
    "/",
    response_model=StudentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_student(
    student_data: StudentCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    # Registration remains disabled until security
    # verification and deployment requirements are met.
    if os.getenv("ENABLE_STUDENT_REGISTRATION") != "true":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Student registration is not enabled.",
        )

    # Prevent caching of registration credentials.
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"

    try:
        student, temporary_password = register_student(
            db,
            student_data,
        )

        return StudentRegistrationResponse(
            student=StudentResponse.model_validate(student),
            temporary_password=temporary_password,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DuplicateStudentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=list[StudentResponse],
)
def list_students(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HOD")),
):
    return get_students(db)