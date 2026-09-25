from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_db,
    require_roles,
)
from backend.app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
)
from backend.app.services.department_service import (
    create_department,
    get_departments,
)


router = APIRouter(
    prefix="/api/departments",
    tags=["Departments"],
)


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    try:
        return create_department(db, department)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=list[DepartmentResponse],
)
def list_departments(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HOD")),
):
    return get_departments(db)