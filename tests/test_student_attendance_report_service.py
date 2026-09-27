
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from datetime import date

from backend.app.models.academic_class import AcademicClass
from backend.app.models.attendance_record import AttendanceRecord
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.department import Department
from backend.app.models.student import Student
from backend.app.models.user import User
from backend.app.services.student_attendance_report_service import (
    StudentAttendanceReportNotFoundError,
    get_student_attendance_report,
)
from sqlalchemy import update
from sqlalchemy import delete
from sqlalchemy import select
from backend.app.services.student_attendance_report_service import (
    StudentAcademicClassNotAssignedError,
)


def test_missing_student_report_is_rejected():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            with pytest.raises(
                StudentAttendanceReportNotFoundError
            ):
                get_student_attendance_report(
                    db=db,
                    student_id=999999,
                )
    finally:
        engine.dispose()


@pytest.fixture
def student_report_environment():
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
                login_id="report_teacher",
                full_name="Report Teacher",
                password_hash="test-hash",
                role="TEACHER",
                is_active=True,
                must_change_password=False,
            )

            student_user = User(
                login_id="report_student",
                full_name="Report Student",
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
                college_id="REPORT001",
                registration_number="REPORT_REG001",
                department="Information Technology",
                class_name="IT-A",
                semester=5,
            )
            db.add(student)
            db.flush()

            sessions = []

            for period in range(1, 5):
                session = AttendanceSession(
                    academic_class_id=academic_class.id,
                    teacher_id=teacher.id,
                    attendance_date=date.today(),
                    period_number=period,
                    status="OPEN",
                )
                db.add(session)
                db.flush()
                sessions.append(session)

            for session, status in zip(
                sessions[:3],
                ["PRESENT", "ABSENT", "LATE"],
            ):
                db.add(
                    AttendanceRecord(
                        session_id=session.id,
                        student_id=student.id,
                        status=status,
                        marked_by="MANUAL",
                    )
                )

            db.commit()

            yield {
                "db": db,
                "student_id": student.id,
            }

    finally:
        engine.dispose()


def test_student_attendance_report_calculations(
    student_report_environment,
):
    env = student_report_environment

    report = get_student_attendance_report(
        db=env["db"],
        student_id=env["student_id"],
    )

    assert report.student_id == env["student_id"]
    assert report.total_sessions == 4
    assert report.present == 1
    assert report.absent == 1
    assert report.od == 0
    assert report.late == 1
    assert report.unmarked == 1
    assert report.attendance_percentage == 50.0


def test_student_without_class_is_rejected(
    student_report_environment,
):
    env = student_report_environment
    db = env["db"]

    db.execute(
        update(Student)
        .where(Student.id == env["student_id"])
        .values(academic_class_id=None)
    )
    db.commit()

    with pytest.raises(
        StudentAcademicClassNotAssignedError
    ):
        get_student_attendance_report(
            db=db,
            student_id=env["student_id"],
        )


def test_student_report_with_no_sessions(
    student_report_environment,
):
    env = student_report_environment
    db = env["db"]

    # Remove attendance records before their sessions.
    db.execute(delete(AttendanceRecord))
    db.execute(delete(AttendanceSession))
    db.commit()

    report = get_student_attendance_report(
        db=db,
        student_id=env["student_id"],
    )

    assert report.total_sessions == 0
    assert report.present == 0
    assert report.absent == 0
    assert report.od == 0
    assert report.late == 0
    assert report.unmarked == 0
    assert report.attendance_percentage == 0.0


def test_student_report_with_od(
    student_report_environment,
):
    env = student_report_environment
    db = env["db"]

    absent_record = db.scalars(
        select(AttendanceRecord).where(
            AttendanceRecord.student_id == env["student_id"],
            AttendanceRecord.status == "ABSENT",
        )
    ).one()

    absent_record.status = "OD"
    db.commit()

    report = get_student_attendance_report(
        db=db,
        student_id=env["student_id"],
    )

    assert report.total_sessions == 4
    assert report.present == 1
    assert report.absent == 0
    assert report.od == 1
    assert report.late == 1
    assert report.unmarked == 1
    assert report.attendance_percentage == 50.0
