from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.department import Department
from backend.app.schemas.department import DepartmentCreate


def create_department(
    db: Session,
    department_data: DepartmentCreate,
) -> Department:
    """Create a department after checking for duplicates."""

    code = department_data.code.strip().upper()
    name = department_data.name.strip()

    if not code or not name:
        raise ValueError(
            "Department code and name cannot be empty."
        )

    existing_department = db.scalar(
        select(Department).where(
            (Department.code == code)
            | (Department.name == name)
        )
    )

    if existing_department is not None:
        raise ValueError(
            "Department code or name already exists."
        )

    department = Department(
        code=code,
        name=name,
    )

    db.add(department)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(department)

    return department


def get_departments(db: Session) -> list[Department]:
    """Retrieve all departments ordered by name."""

    return list(
        db.scalars(
            select(Department).order_by(Department.name)
        ).all()
    )