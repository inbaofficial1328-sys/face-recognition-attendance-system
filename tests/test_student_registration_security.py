from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.models.department import Department
from backend.app.models.academic_class import AcademicClass
from backend.app.schemas.student import StudentCreate
from backend.app.services.student_service import register_student
from backend.app.core.security import verify_password


def test_student_registration_security():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    try:
        Base.metadata.create_all(engine)

        with Session(engine) as db:
            department = Department(
                code="IT",
                name="Information Technology",
            )

            db.add(department)
            db.flush()

            academic_class = AcademicClass(
                department_id=department.id,
                name="Information Technology",
                section="A",
                semester=5,
            )

            db.add(academic_class)
            db.commit()

            student_data = StudentCreate(
                login_id="security_test_student",
                full_name="Security Test Student",
                academic_class_id=academic_class.id,
                college_id="SECURITY001",
                registration_number="REGSECURITY001",
            )

            student, temporary_password = register_student(
                db,
                student_data,
            )

            user = db.get(User, student.user_id)

            assert user is not None
            assert user.role == "STUDENT"
            assert user.must_change_password is True

            assert len(temporary_password) >= 20

            assert verify_password(
                temporary_password,
                user.password_hash,
            )

            assert user.password_hash != temporary_password

            assert student.academic_class_id == academic_class.id
            assert student.department == department.name
            assert student.semester == academic_class.semester

    finally:
        engine.dispose()