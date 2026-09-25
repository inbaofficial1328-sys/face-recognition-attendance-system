
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.academic_class import AcademicClass
from backend.app.models.teacher_assignment import TeacherAssignment
from backend.app.models.user import User
from backend.app.schemas.teacher_assignment import TeacherAssignmentCreate


class InvalidTeacherError(ValueError):
    pass


class AcademicClassNotFoundError(ValueError):
    pass


class DuplicateTeacherAssignmentError(ValueError):
    pass


def create_teacher_assignment(
    db: Session,
    assignment_data: TeacherAssignmentCreate,
) -> TeacherAssignment:

    teacher = db.get(User, assignment_data.teacher_id)

    if teacher is None or teacher.role != "TEACHER":
        raise InvalidTeacherError(
            "A valid teacher account is required."
        )

    if not teacher.is_active:
        raise InvalidTeacherError(
            "Cannot assign an inactive teacher."
        )

    academic_class = db.get(
        AcademicClass,
        assignment_data.academic_class_id,
    )

    if academic_class is None:
        raise AcademicClassNotFoundError(
            "Academic class not found."
        )

    existing_assignment = db.scalar(
        select(TeacherAssignment).where(
            TeacherAssignment.teacher_id
            == assignment_data.teacher_id,
            TeacherAssignment.academic_class_id
            == assignment_data.academic_class_id,
        )
    )

    if existing_assignment is not None:
        raise DuplicateTeacherAssignmentError(
            "Teacher is already assigned to this class."
        )

    assignment = TeacherAssignment(
        teacher_id=assignment_data.teacher_id,
        academic_class_id=assignment_data.academic_class_id,
    )

    try:
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

    except IntegrityError as exc:
        db.rollback()
        raise DuplicateTeacherAssignmentError(
            "Teacher is already assigned to this class."
        ) from exc

    except Exception:
        db.rollback()
        raise

    return assignment


def get_teacher_assignments(
    db: Session,
    teacher_id: int | None = None,
) -> list[TeacherAssignment]:

    statement = select(TeacherAssignment)

    if teacher_id is not None:
        statement = statement.where(
            TeacherAssignment.teacher_id == teacher_id
        )

    statement = statement.order_by(TeacherAssignment.id)

    return list(db.scalars(statement).all())
