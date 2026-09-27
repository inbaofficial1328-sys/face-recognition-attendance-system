from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.models.student_face import StudentFace
from backend.app.services.face_recovery_service import (
    scan_face_storage,
)


def test_recovery_scanner_detects_inconsistencies(tmp_path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    storage = tmp_path / "face_embeddings"
    storage.mkdir()

    with Session(engine) as db:
        db.add_all([
            StudentFace(
                student_id=1,
                consent_recorded=True,
                is_enrolled=True,
            ),
            StudentFace(
                student_id=2,
                consent_recorded=True,
                is_enrolled=False,
            ),
        ])

        db.flush()

        (storage / "student_2.enc").write_bytes(
            b"synthetic_test_data"
        )
        (storage / ".student_2_test.tmp").write_bytes(
            b"temporary_test_data"
        )

        report = scan_face_storage(db, storage)

        assert report.missing_file_student_ids == [1]
        assert report.orphan_file_student_ids == [2]
        assert report.temporary_files == [
            ".student_2_test.tmp"
        ]
        assert report.incomplete_enrollment_student_ids == []

    engine.dispose()

def test_recovery_scanner_detects_incomplete_enrollment(
    tmp_path,
):
    from datetime import datetime, timezone

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    storage = tmp_path / "face_embeddings"
    storage.mkdir()

    with Session(engine) as db:
        db.add(
            StudentFace(
                student_id=3,
                consent_recorded=True,
                is_enrolled=False,
                enrolled_at=datetime.now(timezone.utc),
            )
        )
        db.flush()

        report = scan_face_storage(db, storage)

        assert report.incomplete_enrollment_student_ids == [3]
        assert report.missing_file_student_ids == []
        assert report.orphan_file_student_ids == []
        assert report.temporary_files == []

    engine.dispose()
