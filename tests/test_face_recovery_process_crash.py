import multiprocessing as mp
import os
from pathlib import Path

import numpy as np
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.student_face import StudentFace
from backend.app.services.face_recovery_service import scan_face_storage


def crash_worker(database_path, storage_path, key_path, lock_path, student_id):
    from backend.app.services import face_storage_service as storage
    from backend.app.services import face_enrollment_service as enrollment

    storage.FACE_STORAGE_DIR = Path(storage_path)
    storage.KEY_PATH = Path(key_path)
    enrollment.ENROLLMENT_LOCK_DIR = Path(lock_path)

    original_save = storage.save_face_embedding

    def save_then_crash(student_id, embedding):
        original_save(student_id, embedding)
        os._exit(42)

    storage.save_face_embedding = save_then_crash

    engine = create_engine(
        f"sqlite:///{Path(database_path).as_posix()}",
        connect_args={"timeout": 15},
    )

    with Session(engine) as db:
        enrollment.FaceEnrollmentService().enroll(
            db,
            student_id,
            np.ones((1, 128), dtype=np.float32),
        )


def test_actual_process_crash_after_file_creation(tmp_path):
    database_path = tmp_path / "crash.db"
    storage_path = tmp_path / "embeddings"
    key_path = tmp_path / "test.key"
    lock_path = tmp_path / "locks"

    key_path.write_bytes(Fernet.generate_key())

    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"timeout": 15},
    )
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="crash_test_student",
                password_hash="synthetic_hash",
                full_name="Crash Test Student",
                role="STUDENT",
            )
            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="CRASH001",
                registration_number="CRASHREG001",
                department="Testing",
                class_name="Test Class",
                semester=1,
            )
            db.add(student)
            db.flush()

            student_id = student.id

            db.add(StudentFace(
                student_id=student_id,
                consent_recorded=True,
                is_enrolled=False,
            ))
            db.commit()

        context = mp.get_context("spawn")

        process = context.Process(
            target=crash_worker,
            args=(
                str(database_path),
                str(storage_path),
                str(key_path),
                str(lock_path),
                student_id,
            ),
        )

        try:
            process.start()
            process.join(timeout=30)

            if process.is_alive():
                process.terminate()
                process.join(timeout=10)
                raise AssertionError("Crash worker timed out")

            assert process.exitcode == 42

        finally:
            if process.is_alive():
                process.terminate()
                process.join(timeout=10)
            process.close()

        with Session(engine) as db:
            report = scan_face_storage(db, storage_path)
            record = db.query(StudentFace).filter_by(
                student_id=student_id
            ).one()

            assert record.is_enrolled is False

        assert report.orphan_file_student_ids == [student_id]
        assert (
            storage_path / f"student_{student_id}.enc"
        ).is_file()

    finally:
        engine.dispose()
