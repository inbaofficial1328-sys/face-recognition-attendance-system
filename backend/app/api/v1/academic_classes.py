from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_db, require_roles
from backend.app.schemas.academic_class import (
    AcademicClassCreate,
    AcademicClassResponse,
)
from backend.app.services.academic_class_service import (
    create_academic_class,
    get_academic_classes,
)


router = APIRouter(
    prefix="/api/academic-classes",
    tags=["Academic Classes"],
)


@router.post(
    "/",
    response_model=AcademicClassResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_academic_class(
    class_data: AcademicClassCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    try:
        return create_academic_class(db, class_data)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=list[AcademicClassResponse],
)
def list_academic_classes(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HOD")),
):
    return get_academic_classes(db)