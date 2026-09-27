import numpy as np


class FaceEmbeddingService:
    """Serialize and deserialize SFace embeddings."""

    MODEL_VERSION = "opencv_sface_2021dec"
    EMBEDDING_DIMENSIONS = 128
    SERIALIZED_SIZE = 512

    @classmethod
    def serialize(cls, embedding: np.ndarray) -> bytes:
        if not isinstance(embedding, np.ndarray):
            raise TypeError("Embedding must be a NumPy array.")

        if embedding.shape not in ((128,), (1, 128)):
            raise ValueError("Expected 128-dimensional embedding.")

        if embedding.dtype != np.float32:
            raise ValueError("Expected float32 embedding.")

        if not np.isfinite(embedding).all():
            raise ValueError("Embedding contains invalid values.")

        return embedding.astype(
            "<f4", copy=False
        ).tobytes()

    @classmethod
    def deserialize(cls, data: bytes) -> np.ndarray:
        if not isinstance(data, bytes):
            raise TypeError("Serialized embedding must be bytes.")

        if len(data) != cls.SERIALIZED_SIZE:
            raise ValueError("Invalid serialized embedding size.")

        embedding = np.frombuffer(
            data,
            dtype="<f4",
        ).reshape(1, cls.EMBEDDING_DIMENSIONS).copy()

        if not np.isfinite(embedding).all():
            raise ValueError("Embedding contains invalid values.")

        return embedding