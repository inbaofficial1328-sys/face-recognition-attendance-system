
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.models.academic_class import AcademicClass
from backend.app.models.attendance_correction import AttendanceCorrection
from backend.app.models.attendance_record import AttendanceRecord
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.department import Department
from backend.app.models.student import Student
from backend.app.models.user import User
from backend.app.schemas.attendance_correction import (
    AttendanceCorrectionRequest,
)
from backend.app.services.attendance_correction_service import (
    CorrectionPermissionError,
    CorrectionRecordNotFoundError,
    CorrectionSessionClosedError,
    CorrectionUnchangedStatusError,
    correct_attendance,
)


@pytest.fixture
def correction_environment():
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
                login_id="correction_teacher",
                full_name="Correction Teacher",
                password_hash="test-hash",
                role="TEACHER",
                is_active=True,
                must_change_password=False,
            )

            other_teacher = User(
                login_id="other_correction_teacher",
                full_name="Other Teacher",
                password_hash="test-hash",
                role="TEACHER",
                is_active=True,
                must_change_password=False,
            )

            student_user = User(
                login_id="correction_student",
                full_name="Correction Student",
                password_hash="test-hash",
                role="STUDENT",
                is_active=True,
                must_change_password=False,
            )

            db.add_all([teacher, other_teacher, student_user])
            db.flush()

            student = Student(
                user_id=student_user.id,
                academic_class_id=academic_class.id,
                college_id="CORR001",
                registration_number="CORRREG001",
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
            db.flush()

            original_time = datetime(
                2026, 9, 1, 9, 0, tzinfo=timezone.utc
            )

            record = AttendanceRecord(
                session_id=attendance_session.id,
                student_id=student.id,
                status="ABSENT",
                marked_by="FACE_RECOGNITION",
                marked_at=original_time,
            )
            db.add(record)
            db.commit()

            yield {
                "db": db,
                "record_id": record.id,
                "session_id": attendance_session.id,
                "teacher_id": teacher.id,
                "other_teacher_id": other_teacher.id,
            }

    finally:
        engine.dispose()


def correction_request(status="PRESENT"):
    return AttendanceCorrectionRequest(
        status=status,
        reason="Verified by the class teacher",
    )


def audit_entries(db):
    return db.scalars(
        select(AttendanceCorrection)
        .order_by(AttendanceCorrection.id)
    ).all()


def test_successful_correction_creates_audit_entry(
    correction_environment,
):
    env = correction_environment

    updated = correct_attendance(
        env["db"],
        env["record_id"],
        correction_request(),
        env["teacher_id"],
    )

    assert updated.status == "PRESENT"

    entries = audit_entries(env["db"])
    assert len(entries) == 1

    entry = entries[0]
    assert entry.attendance_record_id == env["record_id"]
    assert entry.corrected_by == env["teacher_id"]
    assert entry.old_status == "ABSENT"
    assert entry.new_status == "PRESENT"
    assert entry.reason == "Verified by the class teacher"
    assert entry.corrected_at is not None


def test_original_marking_details_are_preserved(
    correction_environment,
):
    env = correction_environment
    db = env["db"]

    original = db.get(
        AttendanceRecord,
        env["record_id"],
    )

    original_method = original.marked_by
    original_time = original.marked_at

    correct_attendance(
        db,
        env["record_id"],
        correction_request(),
        env["teacher_id"],
    )

    db.expire_all()

    updated = db.get(
        AttendanceRecord,
        env["record_id"],
    )

    assert updated.status == "PRESENT"
    assert updated.marked_by == original_method
    assert updated.marked_at == original_time


def test_other_teacher_cannot_correct_attendance(
    correction_environment,
):
    env = correction_environment

    with pytest.raises(CorrectionPermissionError):
        correct_attendance(
            env["db"],
            env["record_id"],
            correction_request(),
            env["other_teacher_id"],
        )

    assert env["db"].get(
        AttendanceRecord,
        env["record_id"],
    ).status == "ABSENT"

    assert audit_entries(env["db"]) == []


def test_closed_session_cannot_be_corrected(
    correction_environment,
):
    env = correction_environment
    db = env["db"]

    session = db.get(
        AttendanceSession,
        env["session_id"],
    )
    session.status = "CLOSED"
    db.commit()

    with pytest.raises(CorrectionSessionClosedError):
        correct_attendance(
            db,
            env["record_id"],
            correction_request(),
            env["teacher_id"],
        )

    assert audit_entries(db) == []


def test_unchanged_status_is_rejected(
    correction_environment,
):
    env = correction_environment

    with pytest.raises(CorrectionUnchangedStatusError):
        correct_attendance(
            env["db"],
            env["record_id"],
            correction_request("ABSENT"),
            env["teacher_id"],
        )

    assert audit_entries(env["db"]) == []


def test_missing_record_is_rejected(
    correction_environment,
):
    env = correction_environment

    with pytest.raises(CorrectionRecordNotFoundError):
        correct_attendance(
            env["db"],
            999999,
            correction_request(),
            env["teacher_id"],
        )

    assert audit_entries(env["db"]) == []


def test_multiple_corrections_preserve_history(
    correction_environment,
):
    env = correction_environment

    correct_attendance(
        env["db"],
        env["record_id"],
        correction_request("PRESENT"),
        env["teacher_id"],
    )

    correct_attendance(
        env["db"],
        env["record_id"],
        correction_request("OD"),
        env["teacher_id"],
    )

    entries = audit_entries(env["db"])

    assert len(entries) == 2
    assert (entries[0].old_status, entries[0].new_status) == (
        "ABSENT", "PRESENT"
    )
    assert (entries[1].old_status, entries[1].new_status) == (
        "PRESENT", "OD"
    )
