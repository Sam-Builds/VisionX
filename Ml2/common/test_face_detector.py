
import sys
from pathlib import Path
import cv2

# Add the VisionX project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Ml2.common.face_detector import FaceDetector


VIDEO_PATH = (
    PROJECT_ROOT /
    "Ml2" /
    "activity" /
    "videos" /
    "walking" /
    "abhwalk.mp4"
)

detector = FaceDetector()
cap = cv2.VideoCapture(str(VIDEO_PATH))

if not cap.isOpened():
    raise RuntimeError(f"Cannot open video: {VIDEO_PATH}")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    face_detected, faces = detector.detect(frame)

    for x, y, w, h in faces:
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

    status = (
        "FACE DETECTED"
        if face_detected
        else "NO VISIBLE FACE"
    )

    cv2.putText(
        frame,
        status,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0) if face_detected else (0, 0, 255),
        2
    )

    cv2.imshow("VisionX - Face Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
detector.detector = None
cv2.destroyAllWindows()
