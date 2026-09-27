import pytest

from backend.app.services import face_storage_service as storage


def test_existing_embedding_survives_failed_save(
    tmp_path,
    monkeypatch,
):
    directory = tmp_path / "embeddings"
    directory.mkdir()

    monkeypatch.setattr(
        storage, "FACE_STORAGE_DIR", directory
    )

    class FakeCipher:
        def encrypt(self, data):
            return b"new_encrypted_data"

    monkeypatch.setattr(
        storage, "_get_cipher", lambda: FakeCipher()
    )

    target = directory / "student_1.enc"
    target.write_bytes(b"existing_encrypted_data")

    with pytest.raises(FileExistsError):
        storage.save_face_embedding(
            1, b"synthetic_embedding"
        )

    assert target.read_bytes() == b"existing_encrypted_data"
    assert list(directory.glob("*.tmp")) == []


def test_partial_write_preserves_existing_file(
    tmp_path,
    monkeypatch,
):
    directory = tmp_path / "embeddings"
    directory.mkdir()

    monkeypatch.setattr(
        storage, "FACE_STORAGE_DIR", directory
    )

    class FakeCipher:
        def encrypt(self, data):
            return b"encrypted_synthetic_data"

    monkeypatch.setattr(
        storage, "_get_cipher", lambda: FakeCipher()
    )

    target = directory / "student_1.enc"

    def simulated_link(source, destination):
        target.write_bytes(b"other_operation_data")
        raise FileExistsError(
            "Simulated concurrent publication"
        )

    monkeypatch.setattr(
        storage.os, "link", simulated_link
    )

    with pytest.raises(FileExistsError):
        storage.save_face_embedding(
            1, b"synthetic_embedding"
        )

    assert target.read_bytes() == b"other_operation_data"
    assert list(directory.glob("*.tmp")) == []
