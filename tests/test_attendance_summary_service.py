
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.models.academic_class import AcademicClass
from backend.app.models.attendance_record import AttendanceRecord
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.student import Student
from backend.app.models.user import User
from backend.app.services.attendance_summary_service import (
    AttendanceSummaryNotFoundError,
    AttendanceSummaryPermissionError,
    get_attendance_summary,
)

from backend.app.models.department import Department
from sqlalchemy import delete
from sqlalchemy import select

def test_missing_session_summary_is_rejected():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            with pytest.raises(AttendanceSummaryNotFoundError):
                get_attendance_summary(
                    db=db,
                    session_id=999999,
                    teacher_id=1,
                )
    finally:
        engine.dispose()


def test_attendance_summary_calculations(summary_environment):
    env = summary_environment

    summary = get_attendance_summary(
        db=env["db"],
        session_id=env["session_id"],
        teacher_id=env["teacher_id"],
    )

    assert summary.session_id == env["session_id"]
    assert summary.total_students == 4

    assert summary.present == 1
    assert summary.absent == 1
    assert summary.od == 0
    assert summary.late == 1
    assert summary.unmarked == 1

    assert summary.attendance_percentage == 50.0


@pytest.fixture
def summary_environment():
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
                login_id="summary_teacher",
                full_name="Summary Teacher",
                password_hash="test-hash",
                role="TEACHER",
                is_active=True,
                must_change_password=False,
            )

            other_teacher = User(
                login_id="summary_other_teacher",
                full_name="Other Teacher",
                password_hash="test-hash",
                role="TEACHER",
                is_active=True,
                must_change_password=False,
            )

            db.add_all([teacher, other_teacher])
            db.flush()

            students = []

            for number in range(1, 5):
                student_user = User(
                    login_id=f"summary_student_{number}",
                    full_name=f"Summary Student {number}",
                    password_hash="test-hash",
                    role="STUDENT",
                    is_active=True,
                    must_change_password=False,
                )
                db.add(student_user)
                db.flush()

                student = Student(
                    user_id=student_user.id,
                    academic_class_id=academic_class.id,
                    college_id=f"SUM{number:03d}",
                    registration_number=f"SUMREG{number:03d}",
                    department="Information Technology",
                    class_name="IT-A",
                    semester=5,
                )
                db.add(student)
                db.flush()
                students.append(student)

            attendance_session = AttendanceSession(
                academic_class_id=academic_class.id,
                teacher_id=teacher.id,
                attendance_date=date.today(),
                period_number=1,
                status="OPEN",
            )
            db.add(attendance_session)
            db.flush()

            for student, attendance_status in zip(
                students[:3],
                ["PRESENT", "ABSENT", "LATE"],
            ):
                db.add(
                    AttendanceRecord(
                        session_id=attendance_session.id,
                        student_id=student.id,
                        status=attendance_status,
                        marked_by="MANUAL",
                    )
                )

            db.commit()

            yield {
                "db": db,
                "session_id": attendance_session.id,
                "teacher_id": teacher.id,
                "other_teacher_id": other_teacher.id,
                "student_ids": [
                    student.id for student in students
                ],
            }

    finally:
        engine.dispose()


def test_other_teacher_cannot_view_attendance_summary(
    summary_environment,
):
    env = summary_environment

    with pytest.raises(AttendanceSummaryPermissionError):
        get_attendance_summary(
            db=env["db"],
            session_id=env["session_id"],
            teacher_id=env["other_teacher_id"],
        )


def test_empty_session_attendance_summary(summary_environment):
    env = summary_environment
    db = env["db"]

    db.execute(
        delete(AttendanceRecord).where(
            AttendanceRecord.session_id == env["session_id"]
        )
    )
    db.commit()

    summary = get_attendance_summary(
        db=db,
        session_id=env["session_id"],
        teacher_id=env["teacher_id"],
    )

    assert summary.total_students == 4
    assert summary.present == 0
    assert summary.absent == 0
    assert summary.od == 0
    assert summary.late == 0
    assert summary.unmarked == 4
    assert summary.attendance_percentage == 0.0


def test_od_attendance_summary(summary_environment):
    env = summary_environment
    db = env["db"]

    absent_record = db.scalars(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id == env["session_id"],
            AttendanceRecord.status == "ABSENT",
        )
    ).one()

    absent_record.status = "OD"
    db.commit()

    summary = get_attendance_summary(
        db=db,
        session_id=env["session_id"],
        teacher_id=env["teacher_id"],
    )

    assert summary.total_students == 4
    assert summary.present == 1
    assert summary.absent == 0
    assert summary.od == 1
    assert summary.late == 1
    assert summary.unmarked == 1
    assert summary.attendance_percentage == 50.0
