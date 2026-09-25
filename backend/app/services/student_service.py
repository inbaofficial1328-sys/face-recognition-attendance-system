from secrets import token_urlsafe

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.department import Department
from backend.app.models.academic_class import AcademicClass
from backend.app.schemas.student import StudentCreate, StudentUpdate


class DuplicateStudentError(ValueError):
    pass


def register_student(
    db: Session,
    student_data: StudentCreate,
) -> tuple[Student, str]:

    academic_class = db.get(
        AcademicClass,
        student_data.academic_class_id,
    )

    if academic_class is None:
        raise LookupError("Academic class not found.")

    department = db.get(
        Department,
        academic_class.department_id,
    )

    if department is None:
        raise LookupError("Department not found.")

    login_id = student_data.login_id.strip()
    full_name = student_data.full_name.strip()
    college_id = student_data.college_id.strip()
    registration_number = (
        student_data.registration_number.strip()
    )

    umis_number = (
        student_data.umis_number.strip()
        if student_data.umis_number
        else None
    ) or None

    if not all((
        login_id,
        full_name,
        college_id,
        registration_number,
    )):
        raise ValueError("Required fields cannot be blank.")

    existing_user = db.scalar(
        select(User).where(User.login_id == login_id)
    )

    if existing_user is not None:
        raise DuplicateStudentError(
            "Login ID already exists."
        )

    conditions = [
        Student.college_id == college_id,
        Student.registration_number == registration_number,
    ]

    if umis_number is not None:
        conditions.append(
            Student.umis_number == umis_number
        )

    existing_student = db.scalar(
        select(Student).where(or_(*conditions))
    )

    if existing_student is not None:
        raise DuplicateStudentError(
            "College ID, registration number or UMIS already exists."
        )

    temporary_password = token_urlsafe(24)

    user = User(
        login_id=login_id,
        full_name=full_name,
        password_hash=hash_password(temporary_password),
        role="STUDENT",
        is_active=True,
        must_change_password=True,
    )

    try:
        db.add(user)
        db.flush()

        student = Student(
            user_id=user.id,
            academic_class_id=academic_class.id,
            college_id=college_id,
            registration_number=registration_number,
            umis_number=umis_number,
            department=department.name,
            class_name=academic_class.name,
            semester=academic_class.semester,
            date_of_birth=student_data.date_of_birth,
            blood_group=student_data.blood_group,
            phone_number=student_data.phone_number,
        )

        db.add(student)
        db.commit()
        db.refresh(student)

    except IntegrityError as exc:
        db.rollback()
        raise DuplicateStudentError(
            "Student registration conflicts with an existing record."
        ) from exc

    except Exception:
        db.rollback()
        raise

    return student, temporary_password


def get_students(db: Session) -> list[Student]:
    return list(
        db.scalars(
            select(Student).order_by(Student.id)
        ).all()
    )

def get_student_by_id(
    db: Session,
    student_id: int,
) -> Student | None:
    return db.get(Student, student_id)


def update_student(
    db: Session,
    student_id: int,
    student_data: StudentUpdate,
) -> Student:
    student = db.get(Student, student_id)

    if student is None:
        raise LookupError("Student not found.")

    changes = student_data.model_dump(exclude_unset=True)

    if "academic_class_id" in changes:
        class_id = changes.pop("academic_class_id")

        if class_id is None:
            raise ValueError(
                "Academic class cannot be null."
            )

        academic_class = db.get(AcademicClass, class_id)

        if academic_class is None:
            raise LookupError("Academic class not found.")

        department = db.get(
            Department,
            academic_class.department_id,
        )

        if department is None:
            raise LookupError("Department not found.")

        student.academic_class_id = academic_class.id
        student.department = department.name
        student.class_name = academic_class.name
        student.semester = academic_class.semester

    for field, value in changes.items():
        setattr(student, field, value)

    try:
        db.commit()
        db.refresh(student)
    except Exception:
        db.rollback()
        raise

    return student
