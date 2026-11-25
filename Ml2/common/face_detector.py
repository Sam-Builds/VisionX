
import cv2


class FaceDetector:
    def __init__(self):
        cascade_path = (
            cv2.data.haarcascades +
            "haarcascade_frontalface_default.xml"
        )

        self.detector = cv2.CascadeClassifier(cascade_path)

        if self.detector.empty():
            raise RuntimeError(
                f"Could not load face cascade: {cascade_path}"
            )

        print("Face Detector initialized")

    def detect(self, image):
        """
        Detect visible frontal faces in an image or person crop.

        Returns:
            face_detected: bool
            faces: list of (x, y, width, height)
        """

        if image is None or image.size == 0:
            return False, []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces = self.detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(24, 24)
        )

        face_boxes = [
            (int(x), int(y), int(w), int(h))
            for x, y, w, h in faces
        ]

        return len(face_boxes) > 0, face_boxes
