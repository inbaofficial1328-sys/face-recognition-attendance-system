from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

FACE_STORAGE_DIR = (
    PROJECT_ROOT / "data" / "face_embeddings"
)


def initialize_face_storage() -> Path:
    """Create the private local face storage directory."""
    FACE_STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    return FACE_STORAGE_DIR

from pathlib import Path
from cryptography.fernet import Fernet

PROJECT_ROOT = Path(__file__).resolve().parents[3]

FACE_STORAGE_DIR = PROJECT_ROOT / "data" / "face_embeddings"
KEY_PATH = PROJECT_ROOT / "secrets" / "face_encryption.key"


def initialize_face_storage() -> Path:
    FACE_STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )
    return FACE_STORAGE_DIR


def _get_cipher() -> Fernet:
    if not KEY_PATH.is_file():
        raise FileNotFoundError("Face encryption key is missing")

    return Fernet(KEY_PATH.read_bytes())


def _embedding_path(student_id: int) -> Path:
    if type(student_id) is not int or student_id <= 0:
        raise ValueError("Invalid student ID")

    return FACE_STORAGE_DIR / f"student_{student_id}.enc"


def save_face_embedding(student_id: int, embedding: bytes) -> None:
    if not isinstance(embedding, bytes) or not embedding:
        raise ValueError("Embedding must be non-empty bytes")

    initialize_face_storage()
    encrypted = _get_cipher().encrypt(embedding)

    path = _embedding_path(student_id)

    # Exclusive creation prevents accidental overwriting.
    with path.open("xb") as file:
        file.write(encrypted)


def load_face_embedding(student_id: int) -> bytes:
    path = _embedding_path(student_id)
    return _get_cipher().decrypt(path.read_bytes())


def delete_face_embedding(student_id: int) -> bool:
    path = _embedding_path(student_id)

    if not path.exists():
        return False

    path.unlink()
    return True