
import cv2

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("ERROR: Camera could not be opened.")
    raise SystemExit(1)

print("Camera opened successfully.")
print("Press Q to close the camera window.")

try:
    while True:
        success, frame = camera.read()

        if not success:
            print("ERROR: Unable to read camera frame.")
            break

        cv2.imshow("Face Recognition - Camera Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    camera.release()
    cv2.destroyAllWindows()

print("Camera test finished.")
