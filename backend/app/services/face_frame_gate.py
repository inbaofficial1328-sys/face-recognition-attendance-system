"""Camera-frame validation independent of camera hardware and face models."""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class FrameDecision:
    status: str
    face_count: int

def validate_frame(frame: np.ndarray, face_count: int) -> FrameDecision:
    if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8 or frame.size == 0:
        raise ValueError("Expected nonempty uint8 BGR frame")
    if type(face_count) is not int or face_count < 0:
        raise ValueError("Invalid face count")
    if face_count == 0:
        return FrameDecision("NO_FACE", 0)
    if face_count > 1:
        return FrameDecision("MULTIPLE_FACES", face_count)
    return FrameDecision("SINGLE_FACE_DETECTED_UNVERIFIED", 1)
