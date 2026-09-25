
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_db,
    require_roles,
)
from backend.app.schemas.teacher_assignment import (
    TeacherAssignmentCreate,
    TeacherAssignmentResponse,
)
from backend.app.services.teacher_assignment_service import (
    AcademicClassNotFoundError,
    DuplicateTeacherAssignmentError,
    InvalidTeacherError,
    create_teacher_assignment,
    get_teacher_assignments,
)


router = APIRouter(
    prefix="/api/teacher-assignments",
    tags=["Teacher Assignments"],
)


@router.post(
    "/",
    response_model=TeacherAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_teacher(
    assignment_data: TeacherAssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    try:
        return create_teacher_assignment(
            db,
            assignment_data,
        )

    except InvalidTeacherError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except AcademicClassNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except DuplicateTeacherAssignmentError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=list[TeacherAssignmentResponse],
)
def list_all_teacher_assignments(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    return get_teacher_assignments(db)


@router.get(
    "/me",
    response_model=list[TeacherAssignmentResponse],
)
def list_my_teacher_assignments(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("TEACHER")),
):
    return get_teacher_assignments(
        db,
        teacher_id=current_user.id,
    )
