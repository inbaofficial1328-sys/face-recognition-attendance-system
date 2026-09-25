
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.department import Department
from backend.app.models.academic_class import AcademicClass
from backend.app.schemas.student import StudentUpdate
from backend.app.services.student_service import update_student


def test_student_update_service():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="update_test_student",
                full_name="Update Test Student",
                password_hash="isolated-test-placeholder",
                role="STUDENT",
                is_active=True,
                must_change_password=False,
            )

            department = Department(
                code="IT",
                name="Information Technology",
            )

            db.add_all([user, department])
            db.flush()

            academic_class = AcademicClass(
                department_id=department.id,
                name="Information Technology",
                section="B",
                semester=6,
            )

            db.add(academic_class)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="UPDATE001",
                registration_number="REGUPDATE001",
                department="Previous Department",
                class_name="Previous Class",
                semester=5,
            )

            db.add(student)
            db.commit()

            student_id = student.id
            class_id = academic_class.id

            updated = update_student(
                db,
                student_id,
                StudentUpdate(
                    academic_class_id=class_id,
                    phone_number="9876543210",
                ),
            )

            assert updated.academic_class_id == class_id
            assert updated.department == "Information Technology"
            assert updated.class_name == "Information Technology"
            assert updated.semester == 6
            assert updated.phone_number == "9876543210"

            # Registration identifiers must remain unchanged.
            assert updated.college_id == "UPDATE001"
            assert updated.registration_number == "REGUPDATE001"

            # Invalid academic classes must be rejected.
            with pytest.raises(
                LookupError,
                match="Academic class not found",
            ):
                update_student(
                    db,
                    student_id,
                    StudentUpdate(
                        academic_class_id=999999,
                    ),
                )

            db.rollback()

            # Nonexistent students must be rejected.
            with pytest.raises(
                LookupError,
                match="Student not found",
            ):
                update_student(
                    db,
                    999999,
                    StudentUpdate(
                        phone_number="1234567890",
                    ),
                )

    finally:
        engine.dispose()
