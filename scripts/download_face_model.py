from pathlib import Path
from urllib.request import urlopen
import hashlib

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "face_detection"
    / "blaze_face_short_range.tflite"
)

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_detector/blaze_face_short_range/float16/1/"
    "blaze_face_short_range.tflite"
)

EXPECTED_SHA256 = (
    "b4578f35940bf5a1a655214a1cce5cab"
    "13eba73c1297cd78e1a04c2380b0152f"
)


def verify_model(data: bytes) -> bool:
    return hashlib.sha256(data).hexdigest() == EXPECTED_SHA256


def main():
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    if MODEL_PATH.exists():
        if verify_model(MODEL_PATH.read_bytes()):
            print("Existing BlazeFace model verified successfully.")
            return

        raise RuntimeError(
            "Existing model checksum mismatch. "
            "Review the file before replacing it."
        )

    with urlopen(MODEL_URL, timeout=30) as response:
        model_data = response.read()

    if not verify_model(model_data):
        raise RuntimeError("Downloaded model checksum mismatch.")

    MODEL_PATH.write_bytes(model_data)
    print("BlazeFace model downloaded and verified.")


if __name__ == "__main__":
    main()