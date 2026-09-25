
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.models.academic_class import AcademicClass
from backend.app.models.department import Department
from backend.app.models.user import User
from backend.app.schemas.teacher_assignment import (
    TeacherAssignmentCreate,
)
from backend.app.services.teacher_assignment_service import (
    AcademicClassNotFoundError,
    DuplicateTeacherAssignmentError,
    InvalidTeacherError,
    create_teacher_assignment,
    get_teacher_assignments,
)


@pytest.fixture
def assignment_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            db.add(
                Department(
                    name="Information Technology",
                    code="IT",
                )
            )
            db.flush()

            department = db.query(Department).first()

            db.add(
                AcademicClass(
                    department_id=department.id,
                    name="IT",
                    section="A",
                    semester=5,
                )
            )

            db.add_all(
                [
                    User(
                        login_id="assignment_teacher",
                        full_name="Assignment Teacher",
                        password_hash="test-only-hash",
                        role="TEACHER",
                        is_active=True,
                    ),
                    User(
                        login_id="assignment_admin",
                        full_name="Assignment Admin",
                        password_hash="test-only-hash",
                        role="ADMIN",
                        is_active=True,
                    ),
                    User(
                        login_id="inactive_teacher",
                        full_name="Inactive Teacher",
                        password_hash="test-only-hash",
                        role="TEACHER",
                        is_active=False,
                    ),
                ]
            )

            db.commit()
            yield db

    finally:
        engine.dispose()


def test_create_and_list_teacher_assignments(assignment_db):
    db = assignment_db

    teacher = db.query(User).filter_by(
        login_id="assignment_teacher"
    ).one()

    academic_class = db.query(AcademicClass).first()

    assignment = create_teacher_assignment(
        db,
        TeacherAssignmentCreate(
            teacher_id=teacher.id,
            academic_class_id=academic_class.id,
        ),
    )

    assert assignment.id is not None
    assert assignment.teacher_id == teacher.id

    results = get_teacher_assignments(
        db,
        teacher_id=teacher.id,
    )

    assert len(results) == 1
    assert results[0].id == assignment.id


def test_duplicate_teacher_assignment_rejected(assignment_db):
    db = assignment_db

    teacher = db.query(User).filter_by(
        login_id="assignment_teacher"
    ).one()

    academic_class = db.query(AcademicClass).first()

    data = TeacherAssignmentCreate(
        teacher_id=teacher.id,
        academic_class_id=academic_class.id,
    )

    create_teacher_assignment(db, data)

    with pytest.raises(DuplicateTeacherAssignmentError):
        create_teacher_assignment(db, data)


def test_invalid_teacher_rejected(assignment_db):
    db = assignment_db

    admin = db.query(User).filter_by(
        login_id="assignment_admin"
    ).one()

    academic_class = db.query(AcademicClass).first()

    with pytest.raises(InvalidTeacherError):
        create_teacher_assignment(
            db,
            TeacherAssignmentCreate(
                teacher_id=admin.id,
                academic_class_id=academic_class.id,
            ),
        )


def test_inactive_teacher_rejected(assignment_db):
    db = assignment_db

    teacher = db.query(User).filter_by(
        login_id="inactive_teacher"
    ).one()

    academic_class = db.query(AcademicClass).first()

    with pytest.raises(InvalidTeacherError):
        create_teacher_assignment(
            db,
            TeacherAssignmentCreate(
                teacher_id=teacher.id,
                academic_class_id=academic_class.id,
            ),
        )


def test_missing_class_rejected(assignment_db):
    db = assignment_db

    teacher = db.query(User).filter_by(
        login_id="assignment_teacher"
    ).one()

    with pytest.raises(AcademicClassNotFoundError):
        create_teacher_assignment(
            db,
            TeacherAssignmentCreate(
                teacher_id=teacher.id,
                academic_class_id=999999,
            ),
        )
