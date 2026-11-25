
from ultralytics import YOLO
import cv2

model = YOLO("yolo11n.pt")

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Cannot access camera")
    exit()

print("YOLO is running. Press Q or ESC in the camera window to stop.")

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Camera frame not received.")
            break

        results = model.predict(frame, verbose=False)
        output = results[0].plot()

        cv2.imshow("VisionX - YOLO Detection", output)

        key = cv2.waitKey(1) & 0xFF

        if key in (ord('q'), ord('Q'), 27):
            print("YOLO stopped successfully!")
            break

except KeyboardInterrupt:
    print("\nYOLO interrupted.")

finally:
    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)
    print("Camera released.")
