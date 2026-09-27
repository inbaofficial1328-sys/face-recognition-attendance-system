"""Local opt-in face-count preview; no frames or embeddings saved."""
from pathlib import Path
import cv2
import mediapipe as mp
from backend.app.services.face_frame_gate import validate_frame

MODEL = Path("models/face_detection/blaze_face_short_range.tflite")
def main():
    if not MODEL.is_file():
        raise SystemExit("BlazeFace model missing. Preview unavailable.")
    options = mp.tasks.vision.FaceDetectorOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        min_detection_confidence=0.5,
    )
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        raise SystemExit("Camera unavailable")
    try:
        with mp.tasks.vision.FaceDetector.create_from_options(options) as detector:
            while True:
                ok, frame = camera.read()
                if not ok:
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
                decision = validate_frame(frame, len(result.detections))
                cv2.putText(frame, decision.status, (12, 34), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (255, 255, 255), 2)
                cv2.imshow("Local face-count preview ONLY - Q exits", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        camera.release()
        cv2.destroyAllWindows()
if __name__ == "__main__":
    main()
