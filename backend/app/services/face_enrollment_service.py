from pathlib import Path
from filelock import FileLock
from threading import Lock
from contextlib import contextmanager
from datetime import datetime, timezone

import numpy as np
from sqlalchemy.orm import Session

from backend.app.models.student import Student
from backend.app.models.student_face import StudentFace
from backend.app.services.face_embedding_service import (
    FaceEmbeddingService,
)
from backend.app.services import face_storage_service


class FaceEnrollmentService:
    """Internal service for consent-based face enrollment."""

    def __init__(self):
        self.embedding_service = FaceEmbeddingService()

    def enroll(
        self,
        db: Session,
        student_id: int,
        embedding: np.ndarray,
    ) -> StudentFace:
        if type(student_id) is not int or student_id <= 0:
            raise ValueError("Invalid student ID.")

        with student_enrollment_lock(student_id):
            student = db.get(Student, student_id)

            if student is None:
                raise ValueError("Student does not exist.")

            record = (
                db.query(StudentFace)
                .filter(StudentFace.student_id == student_id)
                .one_or_none()
            )

            if record is None or not record.consent_recorded:
                raise ValueError(
                    "Recorded consent is required before enrollment."
                )

            if record.is_enrolled:
                raise ValueError("Student is already enrolled.")

            serialized = self.embedding_service.serialize(
                embedding
            )

            record.model_version = (
                self.embedding_service.MODEL_VERSION
            )
            record.is_enrolled = True
            record.enrolled_at = datetime.now(timezone.utc)

            file_created = False

            try:
                db.flush()
                face_storage_service.save_face_embedding(
                    student_id,
                    serialized,
                )
                file_created = True
                db.commit()

            except Exception as original_error:
                db.rollback()

                if file_created:
                    try:
                        face_storage_service.delete_face_embedding(
                            student_id
                        )
                    except Exception:
                        raise RuntimeError(
                            "Enrollment failed and encrypted file "
                            "cleanup also failed. Manual recovery "
                            f"is required for student ID {student_id}."
                        ) from original_error

                raise

            db.refresh(record)
            return record


_enrollment_registry_lock = Lock()
_student_enrollment_locks = {}

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENROLLMENT_LOCK_DIR = PROJECT_ROOT / "data" / "enrollment_locks"


@contextmanager
def student_enrollment_lock(student_id: int):
    """
    Serialize enrollment for the same student
    across threads and local server processes.
    """

    if type(student_id) is not int or student_id <= 0:
        raise ValueError("Invalid student ID.")

    with _enrollment_registry_lock:
        thread_lock = _student_enrollment_locks.setdefault(
            student_id,
            Lock(),
        )

    with thread_lock:
        ENROLLMENT_LOCK_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        lock_path = (
            ENROLLMENT_LOCK_DIR
            / f"student_{student_id}.lock"
        )

        with FileLock(str(lock_path), timeout=30):
            yield