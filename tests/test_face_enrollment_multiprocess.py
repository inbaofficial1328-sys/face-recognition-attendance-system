import multiprocessing as mp
from pathlib import Path

import numpy as np
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.database import Base
from backend.app.db import base as model_registry  # noqa: F401
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.student_face import StudentFace
from backend.app.services import face_storage_service as storage
from backend.app.services import face_enrollment_service as enrollment


def enrollment_worker(
    database_path,
    storage_path,
    key_path,
    lock_directory,
    student_id,
    start_event,
    result_queue,
):
    storage.FACE_STORAGE_DIR = Path(storage_path)
    storage.KEY_PATH = Path(key_path)
    enrollment.ENROLLMENT_LOCK_DIR = Path(lock_directory)

    engine = create_engine(
        f"sqlite:///{Path(database_path).as_posix()}",
        connect_args={"timeout": 15},
    )

    try:
        if not start_event.wait(timeout=15):
            result_queue.put("start_timeout")
            return

        with Session(engine) as db:
            try:
                enrollment.FaceEnrollmentService().enroll(
                    db,
                    student_id,
                    np.ones((1, 128), dtype=np.float32),
                )
                result_queue.put("enrolled")

            except ValueError as error:
                if "already enrolled" in str(error):
                    result_queue.put("duplicate")
                else:
                    result_queue.put(
                        f"unexpected_value_error: {error}"
                    )

            except Exception as error:
                result_queue.put(
                    f"unexpected_error: {type(error).__name__}: {error}"
                )

    finally:
        engine.dispose()


def test_cross_process_enrollment(tmp_path):
    context = mp.get_context("spawn")

    database_path = tmp_path / "multiprocess.db"
    storage_path = tmp_path / "embeddings"
    key_path = tmp_path / "test.key"
    lock_directory = tmp_path / "locks"

    key_path.write_bytes(Fernet.generate_key())

    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"timeout": 15},
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="multiprocess_student",
                password_hash="synthetic_test_hash",
                full_name="Multiprocess Test Student",
                role="STUDENT",
            )
            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="MULTIPROCESS001",
                registration_number="MULTIPROCESSREG001",
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

        start_event = context.Event()
        result_queue = context.Queue()

        arguments = (
            str(database_path),
            str(storage_path),
            str(key_path),
            str(lock_directory),
            student_id,
            start_event,
            result_queue,
        )

        processes = [
            context.Process(
                target=enrollment_worker,
                args=arguments,
            )
            for _ in range(2)
        ]

        try:
            for process in processes:
                process.start()

            start_event.set()

            results = [
                result_queue.get(timeout=30)
                for _ in processes
            ]

            for process in processes:
                process.join(timeout=10)

            assert all(
                process.exitcode == 0
                for process in processes
            ), results

            assert sorted(results) == [
                "duplicate",
                "enrolled",
            ], results

        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)

            result_queue.close()
            result_queue.join_thread()

        with Session(engine) as db:
            record = (
                db.query(StudentFace)
                .filter_by(student_id=student_id)
                .one()
            )

            assert record.is_enrolled is True
            assert record.model_version == (
                enrollment.FaceEmbeddingService.MODEL_VERSION
            )

        storage.FACE_STORAGE_DIR = storage_path
        storage.KEY_PATH = key_path

        encrypted_file = (
            storage_path / f"student_{student_id}.enc"
        )

        assert encrypted_file.is_file()

        encrypted_data = encrypted_file.read_bytes()
        serialized = Fernet(
            key_path.read_bytes()
        ).decrypt(encrypted_data)

        embedding = enrollment.FaceEmbeddingService.deserialize(
            serialized
        )

        assert embedding.shape == (1, 128)
        assert np.all(embedding == 1.0)

    finally:
        engine.dispose()
