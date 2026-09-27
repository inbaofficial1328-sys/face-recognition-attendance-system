from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.models.student_face import StudentFace
from backend.app.services.face_recovery_service import (
    scan_face_storage,
)


def test_interrupted_enrollment_after_file_creation(
    tmp_path,
):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    storage = tmp_path / "face_embeddings"
    storage.mkdir()

    # Simulate the database state after a transaction
    # rolls back but its encrypted file remains.
    with Session(engine) as db:
        db.add(
            StudentFace(
                student_id=10,
                consent_recorded=True,
                is_enrolled=False,
            )
        )
        db.commit()

    (storage / "student_10.enc").write_bytes(
        b"synthetic_test_data"
    )

    with Session(engine) as db:
        report = scan_face_storage(db, storage)

    assert report.orphan_file_student_ids == [10]
    assert report.missing_file_student_ids == []
    assert report.temporary_files == []

    # Recovery scanning must not delete the file.
    assert (storage / "student_10.enc").exists()

    engine.dispose()
