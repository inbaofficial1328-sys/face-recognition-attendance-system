import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.student_face import StudentFace
from backend.app.services.face_frame_gate import validate_frame
from backend.app.services.face_identity_review_service import review_probe
from backend.app.services.face_match_policy import MatchPolicy

def test_frame_rejection():
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    assert validate_frame(frame, 0).status == "NO_FACE"
    assert validate_frame(frame, 2).status == "MULTIPLE_FACES"
    assert validate_frame(frame, 1).status == "SINGLE_FACE_DETECTED_UNVERIFIED"
    with pytest.raises(ValueError):
        validate_frame(frame, -1)
    with pytest.raises(ValueError):
        validate_frame(frame.astype(np.float32), 1)

def test_review_is_fail_closed_and_consent_gated():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            user = User(login_id="batch2b_synthetic", password_hash="test", full_name="Synthetic", role="STUDENT")
            db.add(user); db.flush()
            student = Student(user_id=user.id, college_id="B2B001", registration_number="B2BREG001", department="Test", class_name="Test", semester=1)
            db.add(student); db.flush()
            record = StudentFace(student_id=student.id, consent_recorded=True, is_enrolled=True)
            db.add(record); db.commit()
            vector = np.ones((1,128), dtype=np.float32)
            gallery = {student.id: vector}
            policy = MatchPolicy(similarity_threshold=0.8, ambiguity_margin=0.05)
            def check(**kwargs):
                return review_probe(db, vector, gallery, policy, **kwargs)
            assert check(face_count=2).status == "REJECT_FACE_COUNT"
            assert check(face_count=1).status == "VALIDATION_REQUIRED"
            assert check(face_count=1, alignment_validated=True, threshold_validated=True).status == "CANDIDATE_REVIEW"
            record.consent_recorded = False; db.commit()
            assert check(face_count=1, alignment_validated=True, threshold_validated=True).status == "NO_CONSENTED_GALLERY"
            record.consent_recorded = True; record.deletion_pending = True; db.commit()
            assert check(face_count=1, alignment_validated=True, threshold_validated=True).status == "NO_CONSENTED_GALLERY"
    finally:
        engine.dispose()
