
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.models.academic_class import AcademicClass
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.department import Department
from backend.app.models.student import Student
from backend.app.models.user import User
from backend.app.schemas.attendance_record import AttendanceRecordCreate
from backend.app.services.attendance_record_service import (
    AttendanceClassMismatchError,
    AttendancePermissionError,
    AttendanceSessionClosedError,
    AttendanceSessionNotFoundError,
    AttendanceStudentNotFoundError,
    DuplicateAttendanceRecordError,
    mark_manual_attendance,
)

from datetime import date


@pytest.fixture
def attendance_environment():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            department = Department(
                name="Information Technology",
                code="IT",
            )
            db.add(department)
            db.flush()

            academic_class = AcademicClass(
                department_id=department.id,
                name="IT",
                section="A",
                semester=5,
            )
            db.add(academic_class)
            db.flush()

            teacher = User(
                login_id="manual_attendance_teacher",
                full_name="Attendance Teacher",
                password_hash="test-hash",
                role="TEACHER",
                is_active=True,
                must_change_password=False,
            )

            student_user = User(
                login_id="manual_attendance_student",
                full_name="Attendance Student",
                password_hash="test-hash",
                role="STUDENT",
                is_active=True,
                must_change_password=False,
            )

            db.add_all([teacher, student_user])
            db.flush()

            student = Student(
                user_id=student_user.id,
                academic_class_id=academic_class.id,
                college_id="TEST001",
                registration_number="REG001",
                department="Information Technology",
                class_name="IT-A",
                semester=5,
            )
            db.add(student)
            db.flush()

            attendance_session = AttendanceSession(
                academic_class_id=academic_class.id,
                teacher_id=teacher.id,
                attendance_date=date.today(),
                period_number=1,
                status="OPEN",
            )
            db.add(attendance_session)
            db.commit()

            yield (
                db,
                attendance_session.id,
                student.id,
                teacher.id,
            )

    finally:
        engine.dispose()


def attendance_request(session_id, student_id):
    return AttendanceRecordCreate(
        session_id=session_id,
        student_id=student_id,
        status="PRESENT",
    )


def test_teacher_marks_manual_attendance(
    attendance_environment,
):
    db, session_id, student_id, teacher_id = (
        attendance_environment
    )

    record = mark_manual_attendance(
        db,
        attendance_request(session_id, student_id),
        teacher_id,
    )

    assert record.id is not None
    assert record.status == "PRESENT"
    assert record.marked_by == "MANUAL"
    assert record.student_id == student_id


def test_rejects_duplicate_attendance(
    attendance_environment,
):
    db, session_id, student_id, teacher_id = (
        attendance_environment
    )

    request = attendance_request(session_id, student_id)

    mark_manual_attendance(db, request, teacher_id)

    with pytest.raises(DuplicateAttendanceRecordError):
        mark_manual_attendance(db, request, teacher_id)


def test_rejects_wrong_teacher(
    attendance_environment,
):
    db, session_id, student_id, teacher_id = (
        attendance_environment
    )

    with pytest.raises(AttendancePermissionError):
        mark_manual_attendance(
            db,
            attendance_request(session_id, student_id),
            teacher_id + 100,
        )


def test_rejects_closed_session(
    attendance_environment,
):
    db, session_id, student_id, teacher_id = (
        attendance_environment
    )

    attendance_session = db.get(
        AttendanceSession,
        session_id,
    )
    attendance_session.status = "CLOSED"
    db.commit()

    with pytest.raises(AttendanceSessionClosedError):
        mark_manual_attendance(
            db,
            attendance_request(session_id, student_id),
            teacher_id,
        )


def test_rejects_missing_session(
    attendance_environment,
):
    db, _, student_id, teacher_id = attendance_environment

    with pytest.raises(AttendanceSessionNotFoundError):
        mark_manual_attendance(
            db,
            attendance_request(99999, student_id),
            teacher_id,
        )


def test_rejects_missing_student(
    attendance_environment,
):
    db, session_id, _, teacher_id = attendance_environment

    with pytest.raises(AttendanceStudentNotFoundError):
        mark_manual_attendance(
            db,
            attendance_request(session_id, 99999),
            teacher_id,
        )


def test_rejects_student_from_another_class(
    attendance_environment,
):
    db, session_id, student_id, teacher_id = (
        attendance_environment
    )

    student = db.get(Student, student_id)
    student.academic_class_id = None
    db.commit()

    with pytest.raises(AttendanceClassMismatchError):
        mark_manual_attendance(
            db,
            attendance_request(session_id, student_id),
            teacher_id,
        )
