from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import numpy as np
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.database import Base
from backend.app.db import base as model_registry  # noqa: F401
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.student_face import StudentFace
from backend.app.services.face_enrollment_service import (
    FaceEnrollmentService,
)
from backend.app.services import face_storage_service as storage


def test_simultaneous_enrollment(tmp_path, monkeypatch):
    monkeypatch.setattr(
        storage,
        "FACE_STORAGE_DIR",
        tmp_path / "embeddings",
    )
    monkeypatch.setattr(
        storage,
        "KEY_PATH",
        tmp_path / "test.key",
    )

    storage.KEY_PATH.write_bytes(Fernet.generate_key())

    database_path = tmp_path / "concurrency.db"

    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"timeout": 10},
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="concurrent_student",
                password_hash="synthetic_test_hash",
                full_name="Concurrent Test Student",
                role="STUDENT",
            )
            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="CONCURRENT001",
                registration_number="CONCURRENTREG001",
                department="Testing",
                class_name="Test Class",
                semester=1,
            )
            db.add(student)
            db.flush()

            student_id = student.id

            db.add(
                StudentFace(
                    student_id=student_id,
                    consent_recorded=True,
                    is_enrolled=False,
                )
            )
            db.commit()

        start = Barrier(2)

        def attempt_enrollment():
            with Session(engine) as db:
                start.wait(timeout=10)

                try:
                    FaceEnrollmentService().enroll(
                        db,
                        student_id,
                        np.ones((1, 128), dtype=np.float32),
                    )
                    return "enrolled"
                except ValueError as error:
                    if "already enrolled" in str(error):
                        return "duplicate"
                    raise

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(attempt_enrollment)
                for _ in range(2)
            ]

            results = [
                future.result(timeout=20)
                for future in futures
            ]

        assert results.count("enrolled") == 1
        assert results.count("duplicate") == 1

        with Session(engine) as db:
            record = (
                db.query(StudentFace)
                .filter_by(student_id=student_id)
                .one()
            )

            assert record.is_enrolled is True

        assert storage.load_face_embedding(student_id)

    finally:
        engine.dispose()