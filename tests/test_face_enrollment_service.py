import numpy as np
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.models.student import Student
from backend.app.models.student_face import StudentFace
from backend.app.models.user import User
from backend.app.services.face_enrollment_service import (
    FaceEnrollmentService,
)


def test_enrollment_requires_consent():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="test_student_001",
                password_hash="synthetic_test_hash",
                full_name="Synthetic Test Student",
                role="STUDENT",
            )

            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="TEST001",
                registration_number="REGTEST001",
                department="Testing",
                class_name="Test Class",
                semester=1,
            )

            db.add(student)
            db.flush()

            face_record = StudentFace(
                student_id=student.id,
                consent_recorded=False,
                is_enrolled=False,
            )

            db.add(face_record)
            db.commit()

            embedding = np.ones(
                (1, 128),
                dtype=np.float32,
            )

            service = FaceEnrollmentService()

            with pytest.raises(
                ValueError,
                match="Recorded consent is required",
            ):
                service.enroll(
                    db,
                    student.id,
                    embedding,
                )

            db.refresh(face_record)

            assert face_record.is_enrolled is False
            assert face_record.enrolled_at is None

    finally:
        engine.dispose()

def test_successful_face_enrollment(
    tmp_path,
    monkeypatch,
):
    from cryptography.fernet import Fernet

    from backend.app.services import (
        face_storage_service as storage,
    )
    from backend.app.services.face_embedding_service import (
        FaceEmbeddingService,
    )

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

    storage.KEY_PATH.write_bytes(
        Fernet.generate_key()
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="face_test_student",
                password_hash="synthetic_test_hash",
                full_name="Face Test Student",
                role="STUDENT",
            )

            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="FACETEST001",
                registration_number="FACEREG001",
                department="Testing",
                class_name="Test Class",
                semester=1,
            )

            db.add(student)
            db.flush()

            face_record = StudentFace(
                student_id=student.id,
                consent_recorded=True,
                is_enrolled=False,
            )

            db.add(face_record)
            db.commit()

            embedding = np.ones(
                (1, 128),
                dtype=np.float32,
            )

            service = FaceEnrollmentService()

            result = service.enroll(
                db,
                student.id,
                embedding,
            )

            assert result.is_enrolled is True
            assert result.consent_recorded is True
            assert result.enrolled_at is not None
            assert result.model_version == (
                FaceEmbeddingService.MODEL_VERSION
            )

            encrypted_path = (
                storage.FACE_STORAGE_DIR
                / f"student_{student.id}.enc"
            )

            assert encrypted_path.is_file()

            encrypted = encrypted_path.read_bytes()

            assert encrypted != (
                FaceEmbeddingService.serialize(embedding)
            )

            decrypted = storage.load_face_embedding(
                student.id
            )

            restored = FaceEmbeddingService.deserialize(
                decrypted
            )

            assert np.array_equal(
                embedding,
                restored,
            )

    finally:
        engine.dispose()

def test_enrollment_database_failure_cleanup(
    tmp_path,
    monkeypatch,
):
    from cryptography.fernet import Fernet

    from backend.app.services import (
        face_storage_service as storage,
    )

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

    storage.KEY_PATH.write_bytes(
        Fernet.generate_key()
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="failure_test_student",
                password_hash="synthetic_test_hash",
                full_name="Failure Test Student",
                role="STUDENT",
            )

            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="FAILTEST001",
                registration_number="FAILREG001",
                department="Testing",
                class_name="Test Class",
                semester=1,
            )

            db.add(student)
            db.flush()

            face_record = StudentFace(
                student_id=student.id,
                consent_recorded=True,
                is_enrolled=False,
            )

            db.add(face_record)
            db.commit()

            student_id = student.id

            def simulate_commit_failure():
                raise RuntimeError(
                    "Simulated database commit failure"
                )

            monkeypatch.setattr(
                db,
                "commit",
                simulate_commit_failure,
            )

            embedding = np.ones(
                (1, 128),
                dtype=np.float32,
            )

            service = FaceEnrollmentService()

            with pytest.raises(
                RuntimeError,
                match="Simulated database commit failure",
            ):
                service.enroll(
                    db,
                    student_id,
                    embedding,
                )

            encrypted_path = (
                storage.FACE_STORAGE_DIR
                / f"student_{student_id}.enc"
            )

            assert not encrypted_path.exists()

            db.expire_all()

            record = db.query(StudentFace).filter_by(
                student_id=student_id
            ).one()

            assert record.is_enrolled is False
            assert record.enrolled_at is None
            assert record.model_version is None

    finally:
        engine.dispose()

def test_duplicate_enrollment_is_rejected(
    tmp_path,
    monkeypatch,
):
    from cryptography.fernet import Fernet
    from backend.app.services import (
        face_storage_service as storage,
    )

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

    storage.KEY_PATH.write_bytes(
        Fernet.generate_key()
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="duplicate_test_student",
                password_hash="synthetic_test_hash",
                full_name="Duplicate Test Student",
                role="STUDENT",
            )
            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="DUPTEST001",
                registration_number="DUPREG001",
                department="Testing",
                class_name="Test Class",
                semester=1,
            )
            db.add(student)
            db.flush()

            db.add(
                StudentFace(
                    student_id=student.id,
                    consent_recorded=True,
                    is_enrolled=False,
                )
            )
            db.commit()

            student_id = student.id
            service = FaceEnrollmentService()

            first_embedding = np.ones(
                (1, 128),
                dtype=np.float32,
            )

            service.enroll(
                db,
                student_id,
                first_embedding,
            )

            encrypted_path = (
                storage.FACE_STORAGE_DIR
                / f"student_{student_id}.enc"
            )

            original_ciphertext = (
                encrypted_path.read_bytes()
            )

            second_embedding = np.zeros(
                (1, 128),
                dtype=np.float32,
            )

            with pytest.raises(
                ValueError,
                match="already enrolled",
            ):
                service.enroll(
                    db,
                    student_id,
                    second_embedding,
                )

            assert (
                encrypted_path.read_bytes()
                == original_ciphertext
            )

            record = db.query(StudentFace).filter_by(
                student_id=student_id
            ).one()

            assert record.is_enrolled is True

    finally:
        engine.dispose()

def test_enrollment_storage_failure_rolls_back(
    monkeypatch,
):
    from backend.app.services import (
        face_storage_service as storage,
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="storage_failure_student",
                password_hash="synthetic_test_hash",
                full_name="Storage Failure Student",
                role="STUDENT",
            )
            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="STORAGEFAIL001",
                registration_number="STORAGEFAILREG001",
                department="Testing",
                class_name="Test Class",
                semester=1,
            )
            db.add(student)
            db.flush()

            face_record = StudentFace(
                student_id=student.id,
                consent_recorded=True,
                is_enrolled=False,
            )
            db.add(face_record)
            db.commit()

            student_id = student.id

            def simulate_storage_failure(
                student_id,
                embedding,
            ):
                raise OSError(
                    "Simulated encrypted storage failure"
                )

            monkeypatch.setattr(
                storage,
                "save_face_embedding",
                simulate_storage_failure,
            )

            service = FaceEnrollmentService()

            embedding = np.ones(
                (1, 128),
                dtype=np.float32,
            )

            with pytest.raises(
                OSError,
                match="Simulated encrypted storage failure",
            ):
                service.enroll(
                    db,
                    student_id,
                    embedding,
                )

            db.expire_all()

            record = db.query(StudentFace).filter_by(
                student_id=student_id
            ).one()

            assert record.is_enrolled is False
            assert record.enrolled_at is None
            assert record.model_version is None

    finally:
        engine.dispose()

def test_enrollment_rejects_existing_storage_file(
    tmp_path,
    monkeypatch,
):
    from cryptography.fernet import Fernet
    from backend.app.services import (
        face_storage_service as storage,
    )

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

    storage.KEY_PATH.write_bytes(
        Fernet.generate_key()
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="race_test_student",
                password_hash="synthetic_test_hash",
                full_name="Race Test Student",
                role="STUDENT",
            )
            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="RACETEST001",
                registration_number="RACEREG001",
                department="Testing",
                class_name="Test Class",
                semester=1,
            )
            db.add(student)
            db.flush()

            db.add(
                StudentFace(
                    student_id=student.id,
                    consent_recorded=True,
                    is_enrolled=False,
                )
            )
            db.commit()

            student_id = student.id

            # Simulate a file already created by
            # another enrollment operation.
            storage.save_face_embedding(
                student_id,
                b"existing-synthetic-embedding",
            )

            path = (
                storage.FACE_STORAGE_DIR
                / f"student_{student_id}.enc"
            )
            original = path.read_bytes()

            service = FaceEnrollmentService()

            with pytest.raises(FileExistsError):
                service.enroll(
                    db,
                    student_id,
                    np.ones(
                        (1, 128),
                        dtype=np.float32,
                    ),
                )

            assert path.read_bytes() == original

            record = db.get(
                StudentFace,
                1,
            )

            assert record.is_enrolled is False

    finally:
        engine.dispose()

def test_enrollment_flush_failure_rolls_back(
    tmp_path,
    monkeypatch,
):
    from backend.app.services import (
        face_storage_service as storage,
    )

    monkeypatch.setattr(
        storage,
        "FACE_STORAGE_DIR",
        tmp_path / "embeddings",
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="flush_failure_student",
                password_hash="synthetic_test_hash",
                full_name="Flush Failure Student",
                role="STUDENT",
            )
            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="FLUSH001",
                registration_number="FLUSHREG001",
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

            def simulate_flush_failure():
                raise RuntimeError(
                    "Simulated database flush failure"
                )

            monkeypatch.setattr(
                db,
                "flush",
                simulate_flush_failure,
            )

            service = FaceEnrollmentService()

            with pytest.raises(
                RuntimeError,
                match="Simulated database flush failure",
            ):
                service.enroll(
                    db,
                    student_id,
                    np.ones((1, 128), dtype=np.float32),
                )

            assert not db.in_transaction()

            path = (
                storage.FACE_STORAGE_DIR
                / f"student_{student_id}.enc"
            )
            assert not path.exists()

    finally:
        engine.dispose()

def test_enrollment_cleanup_failure(
    tmp_path,
    monkeypatch,
):
    from cryptography.fernet import Fernet
    from backend.app.services import (
        face_storage_service as storage,
    )

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
    storage.KEY_PATH.write_bytes(
        Fernet.generate_key()
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            user = User(
                login_id="cleanup_failure_student",
                password_hash="synthetic_test_hash",
                full_name="Cleanup Failure Student",
                role="STUDENT",
            )
            db.add(user)
            db.flush()

            student = Student(
                user_id=user.id,
                college_id="CLEANUP001",
                registration_number="CLEANUPREG001",
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

            def fail_commit():
                raise RuntimeError(
                    "Simulated database commit failure"
                )

            def fail_cleanup(student_id):
                raise PermissionError(
                    "Simulated encrypted file deletion failure"
                )

            monkeypatch.setattr(
                db,
                "commit",
                fail_commit,
            )
            monkeypatch.setattr(
                storage,
                "delete_face_embedding",
                fail_cleanup,
            )

            with pytest.raises(
                RuntimeError,
                match="Manual recovery is required",
            ) as exc_info:
                FaceEnrollmentService().enroll(
                    db,
                    student_id,
                    np.ones((1, 128), dtype=np.float32),
                )

            assert isinstance(
                exc_info.value.__cause__,
                RuntimeError,
            )

            assert (
                "Simulated database commit failure"
                in str(exc_info.value.__cause__)
            )

            assert not db.in_transaction()

            path = (
                storage.FACE_STORAGE_DIR
                / f"student_{student_id}.enc"
            )
            assert path.exists()

    finally:
        engine.dispose()