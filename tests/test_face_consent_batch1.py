import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from backend.app.db.base import Base
from backend.app.models.student import Student
from backend.app.models.user import User
from backend.app.services.face_consent_service import grant_consent, withdraw_consent
from backend.app.services.face_recovery_actions import recheck_student
from backend.app.services import face_storage_service as storage

def test_grant_withdraw_and_locked_recheck(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "FACE_STORAGE_DIR", tmp_path / "faces")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(login_id="consent_test_user", password_hash="synthetic", full_name="Test", role="STUDENT")
        admin = User(login_id="consent_test_admin", password_hash="synthetic", full_name="Admin", role="ADMIN")
        db.add_all([user, admin]); db.flush()
        student = Student(user_id=user.id, college_id="TEST_CONSENT", registration_number="REG_CONSENT", department="Test", class_name="Test", semester=1)
        db.add(student); db.commit()
        with pytest.raises(ValueError):
            grant_consent(db, student.id, admin.id, "")
        record = grant_consent(db, student.id, admin.id, "verified-synthetic-test")
        assert record.consent_at is not None and record.consent_actor_id == admin.id
        assert recheck_student(db, student.id) == "CONSISTENT"
        record = withdraw_consent(db, student.id, admin.id)
        assert record.consent_recorded is False and record.deletion_pending is False
        assert record.consent_withdrawn_at is not None
    engine.dispose()

def test_withdrawal_failure_stays_pending(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "FACE_STORAGE_DIR", tmp_path / "faces")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(login_id="fail_user", password_hash="synthetic", full_name="Test", role="STUDENT")
        admin = User(login_id="fail_admin", password_hash="synthetic", full_name="Admin", role="ADMIN")
        db.add_all([user, admin]); db.flush()
        student = Student(user_id=user.id, college_id="TEST_FAIL", registration_number="REG_FAIL", department="Test", class_name="Test", semester=1)
        db.add(student); db.commit()
        grant_consent(db, student.id, admin.id, "verified-test")
        original = storage.delete_face_embedding
        def fail(_): raise PermissionError("synthetic failure")
        monkeypatch.setattr(storage, "delete_face_embedding", fail)
        with pytest.raises(PermissionError): withdraw_consent(db, student.id, admin.id)
        assert recheck_student(db, student.id) == "DELETION_PENDING"
        monkeypatch.setattr(storage, "delete_face_embedding", original)
        record = withdraw_consent(db, student.id, admin.id)
        assert not record.deletion_pending
    engine.dispose()
