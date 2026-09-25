from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.department import Department
from backend.app.models.academic_class import AcademicClass
from backend.app.schemas.academic_class import AcademicClassCreate


def create_academic_class(
    db: Session,
    class_data: AcademicClassCreate,
) -> AcademicClass:

    department = db.get(
        Department,
        class_data.department_id,
    )

    if department is None:
        raise LookupError(
            "The selected department does not exist."
        )

    name = class_data.name.strip()
    section = class_data.section.strip().upper()

    if not name or not section:
        raise ValueError(
            "Class name and section cannot be empty."
        )

    existing_class = db.scalar(
        select(AcademicClass).where(
            AcademicClass.department_id
            == class_data.department_id,
            AcademicClass.name == name,
            AcademicClass.section == section,
            AcademicClass.semester == class_data.semester,
        )
    )

    if existing_class is not None:
        raise ValueError(
            "This academic class already exists."
        )

    academic_class = AcademicClass(
        department_id=class_data.department_id,
        name=name,
        section=section,
        semester=class_data.semester,
    )

    db.add(academic_class)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError(
            "This academic class already exists."
        ) from exc
    except Exception:
        db.rollback()
        raise

    db.refresh(academic_class)

    return academic_class


def get_academic_classes(
    db: Session,
) -> list[AcademicClass]:

    return list(
        db.scalars(
            select(AcademicClass).order_by(
                AcademicClass.department_id,
                AcademicClass.name,
                AcademicClass.section,
                AcademicClass.semester,
            )
        ).all()
    )