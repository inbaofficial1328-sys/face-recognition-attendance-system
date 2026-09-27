import cv2
import numpy as np


class FaceAlignmentService:
    """Experimental eye-based alignment for SFace."""

    OUTPUT_SIZE = (112, 112)

    # Reference eye positions in the aligned image.
    LEFT_EYE_TARGET = (38.2946, 51.6963)
    RIGHT_EYE_TARGET = (73.5318, 51.5014)

    def align_face(
        self,
        frame: np.ndarray,
        left_eye: tuple[float, float],
        right_eye: tuple[float, float],
    ) -> np.ndarray:

        if not isinstance(frame, np.ndarray):
            raise TypeError("Frame must be a NumPy array.")

        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("Expected a BGR image.")

        if frame.dtype != np.uint8:
            raise ValueError("Expected uint8 image.")

        source = np.asarray(
            [left_eye, right_eye],
            dtype=np.float32,
        )

        if not np.isfinite(source).all():
            raise ValueError("Invalid eye coordinates.")

        if np.linalg.norm(source[1] - source[0]) < 1:
            raise ValueError("Eye positions are too close.")

        target = np.asarray(
            [
                self.LEFT_EYE_TARGET,
                self.RIGHT_EYE_TARGET,
            ],
            dtype=np.float32,
        )

        source_vector = source[1] - source[0]
        target_vector = target[1] - target[0]

        source_angle = np.arctan2(
            source_vector[1],
            source_vector[0],
        )

        target_angle = np.arctan2(
            target_vector[1],
            target_vector[0],
        )

        scale = (
            np.linalg.norm(target_vector)
            / np.linalg.norm(source_vector)
        )

        angle = target_angle - source_angle

        cosine = scale * np.cos(angle)
        sine = scale * np.sin(angle)

        rotation = np.array(
            [
                [cosine, -sine],
                [sine, cosine],
            ],
            dtype=np.float32,
        )

        translation = target[0] - rotation @ source[0]

        matrix = np.column_stack(
            [rotation, translation]
        )

        return cv2.warpAffine(
            frame,
            matrix,
            self.OUTPUT_SIZE,
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
        )