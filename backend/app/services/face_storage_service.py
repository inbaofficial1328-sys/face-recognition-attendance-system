from pathlib import Path

from cryptography.fernet import Fernet


PROJECT_ROOT = Path(__file__).resolve().parents[3]

FACE_STORAGE_DIR = (
    PROJECT_ROOT / "data" / "face_embeddings"
)

KEY_PATH = (
    PROJECT_ROOT / "secrets" / "face_encryption.key"
)


def initialize_face_storage() -> Path:
    """Create the private face storage directory."""
    FACE_STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    return FACE_STORAGE_DIR


def _get_cipher() -> Fernet:
    """Load the existing encryption key."""
    if not KEY_PATH.is_file():
        raise FileNotFoundError(
            "Face encryption key is missing"
        )

    return Fernet(KEY_PATH.read_bytes())


def _embedding_path(student_id: int) -> Path:
    """Validate the student ID and construct its storage path."""
    if type(student_id) is not int or student_id <= 0:
        raise ValueError("Invalid student ID")

    return (
        FACE_STORAGE_DIR
        / f"student_{student_id}.enc"
    )


def save_face_embedding(
    student_id: int,
    embedding: bytes,
) -> None:
    if not isinstance(embedding, bytes) or not embedding:
        raise ValueError(
            "Embedding must be non-empty bytes"
        )

    # Validate the student ID before writing.
    path = _embedding_path(student_id)

    initialize_face_storage()
    encrypted = _get_cipher().encrypt(embedding)

    try:
        with path.open("xb") as file:
            file.write(encrypted)
            file.flush()
            import os
            os.fsync(file.fileno())

    except Exception:
        # Do not delete an existing file if exclusive
        # creation failed because it already exists.
        import sys

        if not isinstance(
            sys.exc_info()[1],
            FileExistsError,
        ):
            path.unlink(missing_ok=True)

        raise


def load_face_embedding(student_id: int) -> bytes:
    """Load and decrypt an existing embedding."""
    path = _embedding_path(student_id)

    return _get_cipher().decrypt(
        path.read_bytes()
    )


def delete_face_embedding(student_id: int) -> bool:
    """Delete a stored embedding."""
    path = _embedding_path(student_id)

    if not path.exists():
        return False

    path.unlink()
    return True