"""Conservative locked recheck; no automated biometric deletion."""
from sqlalchemy.orm import Session
from backend.app.models.student_face import StudentFace
from backend.app.services.face_enrollment_service import student_enrollment_lock
from backend.app.services import face_storage_service

def recheck_student(db: Session, student_id: int) -> str:
    with student_enrollment_lock(student_id):
        db.expire_all()
        record = db.query(StudentFace).filter_by(student_id=student_id).one_or_none()
        exists = face_storage_service._embedding_path(student_id).is_file()
        if record is not None and record.deletion_pending:
            return "DELETION_PENDING"
        if exists and (record is None or not record.is_enrolled):
            return "ORPHAN_MANUAL_REVIEW"
        if not exists and record is not None and record.is_enrolled:
            return "MISSING_MANUAL_REVIEW"
        return "CONSISTENT"
