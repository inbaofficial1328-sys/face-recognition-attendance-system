"""Consent and deletion coordination. Caller must enforce authorization."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.student import Student
from backend.app.models.student_face import StudentFace
from backend.app.models.face_consent_audit import FaceConsentAudit
from backend.app.services.face_enrollment_service import student_enrollment_lock
from backend.app.services import face_storage_service

def grant_consent(db: Session, student_id: int, actor_id: int, reference: str) -> StudentFace:
    if not reference or not reference.strip() or len(reference) > 150:
        raise ValueError("Verified consent reference is required (max 150 characters).")
    with student_enrollment_lock(student_id):
        if db.get(Student, student_id) is None:
            raise LookupError("Student not found")
        record = db.query(StudentFace).filter_by(student_id=student_id).one_or_none()
        if record is None:
            record = StudentFace(student_id=student_id, is_enrolled=False, consent_recorded=False)
            db.add(record)
        if record.is_enrolled or record.deletion_pending or face_storage_service._embedding_path(student_id).exists():
            raise ValueError("Existing or pending biometric data requires manual review")
        record.consent_recorded = True
        record.consent_at = datetime.now(timezone.utc)
        record.consent_actor_id = actor_id
        record.consent_reference = reference.strip()
        record.consent_withdrawn_at = None
        db.add(FaceConsentAudit(student_id=student_id, actor_id=actor_id, action="GRANTED", reference=reference.strip()))
        db.commit()
        db.refresh(record)
        return record

def withdraw_consent(db: Session, student_id: int, actor_id: int) -> StudentFace:
    """Persist withdrawal BEFORE deleting files; retry pending deletions safely."""
    with student_enrollment_lock(student_id):
        record = db.query(StudentFace).filter_by(student_id=student_id).one_or_none()
        if record is None:
            raise LookupError("No face enrollment record")
        if record.consent_withdrawn_at is None:
            record.consent_withdrawn_at = datetime.now(timezone.utc)
            record.consent_recorded = False
            record.deletion_pending = True
            db.add(FaceConsentAudit(student_id=student_id, actor_id=actor_id, action="WITHDRAWN"))
            db.commit()
        # A failed unlink leaves deletion_pending True and enrollment blocked.
        face_storage_service.delete_face_embedding(student_id)
        record.is_enrolled = False
        record.model_version = None
        record.enrolled_at = None
        record.deletion_pending = False
        db.add(FaceConsentAudit(student_id=student_id, actor_id=actor_id, action="DELETION_COMPLETED"))
        db.commit()
        db.refresh(record)
        return record
