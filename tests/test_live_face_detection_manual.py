
from pathlib import Path

import cv2
import mediapipe as mp


MODEL_PATH = Path(
    "models/face_detection/blaze_face_short_range.tflite"
)

if not MODEL_PATH.is_file():
    raise FileNotFoundError(
        f"Face detection model not found: {MODEL_PATH}"
    )

options = mp.tasks.vision.FaceDetectorOptions(
    base_options=mp.tasks.BaseOptions(
        model_asset_path=str(MODEL_PATH)
    ),
    running_mode=mp.tasks.vision.RunningMode.IMAGE,
    min_detection_confidence=0.5,
)

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    raise RuntimeError("Unable to open camera.")

print("Camera opened successfully.")
print("Position your face in front of the camera.")
print("Press Q to exit.")

try:
    with mp.tasks.vision.FaceDetector.create_from_options(
        options
    ) as detector:

        while True:
            success, frame = camera.read()

            if not success:
                print("Unable to read camera frame.")
                break

            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB,
            )

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame,
            )

            result = detector.detect(mp_image)

            for detection in result.detections:
                bbox = detection.bounding_box

                x1 = max(0, bbox.origin_x)
                y1 = max(0, bbox.origin_y)
                x2 = min(
                    frame.shape[1],
                    bbox.origin_x + bbox.width,
                )
                y2 = min(
                    frame.shape[0],
                    bbox.origin_y + bbox.height,
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )

            cv2.putText(
                frame,
                f"Faces detected: {len(result.detections)}",
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            cv2.imshow(
                "Student Attendance - Face Detection",
                frame,
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

finally:
    camera.release()
    cv2.destroyAllWindows()

print("Live face detection test completed.")
