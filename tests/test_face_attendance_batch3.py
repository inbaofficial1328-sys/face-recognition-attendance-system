from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.models.academic_class import AcademicClass
from backend.app.models.attendance_record import AttendanceRecord
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.department import Department
from backend.app.models.student import Student
from backend.app.models.user import User
from backend.app.services.face_attendance_service import (
    FaceAttendanceClassMismatchError,
    FaceAttendanceDuplicateError,
    FaceAttendanceSessionError,
    VerifiedFaceIdentity,
    mark_verified_face_attendance,
)


def make_environment():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = Session(engine)

    department = Department(name="IT", code="FACE3")
    db.add(department)
    db.flush()

    class_a = AcademicClass(
        department_id=department.id, name="IT", section="A", semester=5
    )
    class_b = AcademicClass(
        department_id=department.id, name="IT", section="B", semester=5
    )
    db.add_all([class_a, class_b])
    db.flush()

    teacher = User(
        login_id="face3_teacher", full_name="Batch 3 Teacher",
        password_hash="test-hash", role="TEACHER",
        is_active=True, must_change_password=False,
    )
    user_a = User(
        login_id="face3_student_a", full_name="Student A",
        password_hash="test-hash", role="STUDENT",
        is_active=True, must_change_password=False,
    )
    user_b = User(
        login_id="face3_student_b", full_name="Student B",
        password_hash="test-hash", role="STUDENT",
        is_active=True, must_change_password=False,
    )
    db.add_all([teacher, user_a, user_b])
    db.flush()

    student_a = Student(
        user_id=user_a.id, academic_class_id=class_a.id,
        college_id="FACE3001", registration_number="FACE3REG001",
        department="IT", class_name="IT-A", semester=5,
    )
    student_b = Student(
        user_id=user_b.id, academic_class_id=class_b.id,
        college_id="FACE3002", registration_number="FACE3REG002",
        department="IT", class_name="IT-B", semester=5,
    )
    db.add_all([student_a, student_b])
    db.flush()

    attendance_session = AttendanceSession(
        academic_class_id=class_a.id, teacher_id=teacher.id,
        attendance_date=date.today(), period_number=1, status="OPEN",
    )
    db.add(attendance_session)
    db.commit()
    return engine, db, student_a, student_b, attendance_session


def identity(student_id):
    return VerifiedFaceIdentity(
        student_id=student_id,
        verified=True,
        verification_source="validated_face_pipeline",
    )


def test_verified_identity_marks_present():
    engine, db, student, _, session = make_environment()
    try:
        record = mark_verified_face_attendance(db, session.id, identity(student.id))
        assert record.status == "PRESENT"
        assert record.marked_by == "FACE_RECOGNITION"
    finally:
        db.close()
        engine.dispose()


def test_unverified_or_untrusted_identity_is_rejected():
    with pytest.raises(ValueError):
        VerifiedFaceIdentity(1, False, "validated_face_pipeline")
    with pytest.raises(ValueError):
        VerifiedFaceIdentity(1, True, "caller_supplied")


def test_duplicate_is_rejected_and_only_one_record_remains():
    engine, db, student, _, session = make_environment()
    try:
        mark_verified_face_attendance(db, session.id, identity(student.id))
        with pytest.raises(FaceAttendanceDuplicateError):
            mark_verified_face_attendance(db, session.id, identity(student.id))
        assert db.query(AttendanceRecord).count() == 1
    finally:
        db.close()
        engine.dispose()


def test_wrong_class_is_rejected():
    engine, db, _, other_student, session = make_environment()
    try:
        with pytest.raises(FaceAttendanceClassMismatchError):
            mark_verified_face_attendance(db, session.id, identity(other_student.id))
        assert db.query(AttendanceRecord).count() == 0
    finally:
        db.close()
        engine.dispose()


def test_closed_session_is_rejected():
    engine, db, student, _, session = make_environment()
    try:
        session.status = "CLOSED"
        db.commit()
        with pytest.raises(FaceAttendanceSessionError):
            mark_verified_face_attendance(db, session.id, identity(student.id))
        assert db.query(AttendanceRecord).count() == 0
    finally:
        db.close()
        engine.dispose()
