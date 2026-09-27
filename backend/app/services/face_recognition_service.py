from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "face_recognition"
    / "face_recognition_sface_2021dec.onnx"
)


class FaceRecognitionService:
    """Generate SFace embeddings from aligned face images."""

    MODEL_VERSION = "opencv_sface_2021dec"

    def __init__(self):
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                "SFace model not found: "
                f"{MODEL_PATH}"
            )

        self.recognizer = cv2.FaceRecognizerSF.create(
            str(MODEL_PATH),
            ""
        )

    def generate_embedding(
        self,
        aligned_face: np.ndarray
    ) -> np.ndarray:
        if not isinstance(aligned_face, np.ndarray):
            raise TypeError("Face must be a NumPy array.")

        if aligned_face.shape != (112, 112, 3):
            raise ValueError(
                "Expected a 112x112 BGR face image."
            )

        if aligned_face.dtype != np.uint8:
            raise ValueError(
                "Face image must have uint8 data type."
            )

        embedding = self.recognizer.feature(
            aligned_face
        )

        if embedding.shape != (1, 128):
            raise RuntimeError(
                "Unexpected face embedding dimensions."
            )

        if not np.isfinite(embedding).all():
            raise RuntimeError(
                "Face embedding contains invalid values."
            )

        return embedding.astype(
            np.float32,
            copy=False
        )