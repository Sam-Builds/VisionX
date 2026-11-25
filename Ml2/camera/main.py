
import argparse
import sys
import time
from pathlib import Path
from collections import deque

import cv2
import numpy as np
import torch
import torch.nn as nn


# --------------------------------------------------
# PATHS AND IMPORTS
# --------------------------------------------------

ML2_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML2_DIR))

from tracking.tracker import PersonTracker
from pose.pose_detector import PoseDetector
from common.face_detector import FaceDetector


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

FRAME_STRIDE = 4
NUM_PEOPLE = 2

MODEL_PATH = (
    ML2_DIR
    / "activity"
    / "models"
    / "activity_lstm.pth"
)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

RISK_SCORES = {
    "WALKING": 10,
    "RUNNING": 30,
    "FIGHTING": 65,
    "VIOLENCE": 95,
    "UNKNOWN": 0
}

CONFIDENCE_THRESHOLD = 0.55


# --------------------------------------------------
# LSTM MODEL
# --------------------------------------------------

class ActivityLSTM(nn.Module):

    def __init__(self, input_size, num_classes):
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=64,
            num_layers=1,
            batch_first=True
        )

        self.classifier = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        output, _ = self.lstm(x)
        last_output = output[:, -1, :]
        return self.classifier(last_output)


# --------------------------------------------------
# ACTIVITY PREDICTOR
# --------------------------------------------------

class ActivityPredictor:

    def __init__(self):

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}"
            )

        checkpoint = torch.load(
            MODEL_PATH,
            map_location=DEVICE,
            weights_only=False
        )

        self.classes = checkpoint["classes"]
        self.window_size = checkpoint["window_size"]
        self.num_people = checkpoint["num_people"]
        self.input_size = checkpoint["input_size"]

        self.model = ActivityLSTM(
            input_size=self.input_size,
            num_classes=len(self.classes)
        ).to(DEVICE)

        self.model.load_state_dict(
            checkpoint["model_state_dict"]
        )

        self.model.eval()

        self.sequence = deque(
            maxlen=self.window_size
        )

        self.prediction_history = deque(
            maxlen=5
        )

        print("Activity LSTM loaded.")
        print("Device:", DEVICE)
        print("Classes:", self.classes)

    def build_frame_features(
        self,
        people,
        frame,
        pose_detector
    ):

        height, width = frame.shape[:2]

        selected_people = sorted(
            people,
            key=lambda person: person["id"]
        )[:self.num_people]

        person_features = []

        for person in selected_people:

            x1, y1, x2, y2 = person["bbox"]

            x1 = max(0, min(x1, width - 1))
            x2 = max(0, min(x2, width))
            y1 = max(0, min(y1, height - 1))
            y2 = max(0, min(y2, height))

            if x2 <= x1 or y2 <= y1:
                continue

            crop = frame[y1:y2, x1:x2]

            pose = pose_detector.detect(crop)

            if pose is None:
                continue

            landmarks = pose["landmarks"]

            if landmarks.shape != (33, 4):
                continue

            person_features.append(
                landmarks.reshape(-1)
            )

        if not person_features:
            return None

        while len(person_features) < self.num_people:

            person_features.append(
                np.zeros(33 * 4, dtype=np.float32)
            )

        combined = np.concatenate(
            person_features[:self.num_people]
        )

        return combined.astype(np.float32)

    def update(self, frame_features):

        if frame_features is None:
            return "UNKNOWN", 0.0

        self.sequence.append(frame_features)

        if len(self.sequence) < self.window_size:
            return "UNKNOWN", 0.0

        sequence = np.asarray(
            self.sequence,
            dtype=np.float32
        )

        if sequence.shape != (
            self.window_size,
            self.input_size
        ):
            return "UNKNOWN", 0.0

        input_tensor = torch.from_numpy(
            sequence
        ).unsqueeze(0).to(DEVICE)

        with torch.no_grad():

            logits = self.model(input_tensor)

            probabilities = torch.softmax(
                logits,
                dim=1
            )[0]

        probabilities = probabilities.cpu().numpy()

        self.prediction_history.append(
            probabilities
        )

        average_probabilities = np.mean(
            np.asarray(self.prediction_history),
            axis=0
        )

        best_index = int(
            np.argmax(average_probabilities)
        )

        confidence = float(
            average_probabilities[best_index]
        )

        if confidence < CONFIDENCE_THRESHOLD:
            return "UNKNOWN", confidence

        activity = self.classes[best_index].upper()

        return activity, confidence

    def reset(self):
        self.sequence.clear()
        self.prediction_history.clear()


# --------------------------------------------------
# SOURCE PARSER
# --------------------------------------------------

def parse_source(value):

    if value.isdigit():
        return int(value)

    return value


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source",
        default="0"
    )

    args = parser.parse_args()

    source = parse_source(args.source)
    is_video = isinstance(source, str)

    print("=" * 55)
    print("              VISIONX ML2")
    print("=" * 55)

    print("Initializing YOLO...")
    tracker = PersonTracker()

    print("Initializing MediaPipe...")
    pose_detector = PoseDetector()

    print("Initializing Face Detector...")
    face_detector = FaceDetector()

    print("Loading Activity LSTM...")
    activity_predictor = ActivityPredictor()

    cap = cv2.VideoCapture(source)

    if not cap.isOpened():

        print("ERROR: Could not open source.")

        pose_detector.close()
        cap.release()
        return

    fps = cap.get(cv2.CAP_PROP_FPS)

    if not fps or fps <= 0 or fps > 120:
        fps = 30.0

    playback_interval = FRAME_STRIDE / fps

    print(f"Source FPS: {fps:.2f}")
    print(
        f"Inference sampling: "
        f"{fps / FRAME_STRIDE:.2f} FPS"
    )

    print("LSTM activity recognition enabled.")
    print("Risk-based bounding box colors enabled.")
    print("Press Q to quit.")

    start_wall = None
    first_timestamp = None

    try:

        while True:

            iteration_start = time.monotonic()

            success, frame = cap.read()

            if not success:
                print("Video ended.")
                break

            if is_video:

                timestamp = (
                    cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                )

                if start_wall is None:
                    start_wall = time.monotonic()
                    first_timestamp = timestamp

                timestamp -= first_timestamp

            else:

                timestamp = time.monotonic()

            # --------------------------------
            # 1. PERSON DETECTION
            # --------------------------------

            people = tracker.detect(frame)

            height, width = frame.shape[:2]

            # --------------------------------
            # 2. SCENE ACTIVITY PREDICTION
            # --------------------------------

            frame_features = (
                activity_predictor.build_frame_features(
                    people,
                    frame,
                    pose_detector
                )
            )

            activity, confidence = activity_predictor.update(
                frame_features
            )

            score = RISK_SCORES.get(
                activity,
                0
            )

            # --------------------------------
            # 3. RISK COLOR
            # --------------------------------

            if score > 50:
                risk_color = (0, 0, 255)       # RED
            else:
                risk_color = (0, 255, 0)       # GREEN

            # --------------------------------
            # 4. PERSON BOXES + FACE DETECTION
            # --------------------------------

            for person in people:

                track_id = person["id"]

                x1, y1, x2, y2 = person["bbox"]

                x1 = max(0, min(x1, width - 1))
                x2 = max(0, min(x2, width))
                y1 = max(0, min(y1, height - 1))
                y2 = max(0, min(y2, height))

                if x2 <= x1 or y2 <= y1:
                    continue

                crop = frame[y1:y2, x1:x2]

                face_detected, faces = face_detector.detect(
                    crop
                )

                for fx, fy, fw, fh in faces:

                    cv2.rectangle(
                        frame,
                        (x1 + fx, y1 + fy),
                        (x1 + fx + fw, y1 + fy + fh),
                        (255, 0, 255),
                        2
                    )

                # Bounding box changes with risk.
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    risk_color,
                    2
                )

                person_label = (
                    f"ID {track_id} | {activity}"
                )

                cv2.putText(
                    frame,
                    person_label,
                    (x1, max(25, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    risk_color,
                    2
                )

                face_status = (
                    "FACE VISIBLE"
                    if face_detected
                    else "FACE NOT VISIBLE"
                )

                cv2.putText(
                    frame,
                    face_status,
                    (x1, min(height - 10, y2 + 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (255, 0, 255)
                    if face_detected
                    else (0, 165, 255),
                    1
                )

            # --------------------------------
            # 5. SCENE INFORMATION
            # --------------------------------

            if activity == "UNKNOWN":
                activity_color = (180, 180, 180)
            else:
                activity_color = risk_color

            cv2.rectangle(
                frame,
                (10, 45),
                (width - 10, 120),
                (30, 30, 30),
                -1
            )

            scene_label = (
                f"SCENE: {activity} | "
                f"RISK: {score}/100"
            )

            cv2.putText(
                frame,
                scene_label,
                (20, 78),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.72,
                activity_color,
                2
            )

            confidence_label = (
                f"Model confidence: "
                f"{confidence * 100:.1f}%"
            )

            cv2.putText(
                frame,
                confidence_label,
                (20, 106),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (255, 255, 255),
                1
            )

            # --------------------------------
            # 6. PROCESSING FPS
            # --------------------------------

            processing_time = (
                time.monotonic() - iteration_start
            )

            processing_fps = 1.0 / max(
                processing_time,
                0.0001
            )

            cv2.putText(
                frame,
                f"VISIONX | FPS: {processing_fps:.1f}",
                (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.58,
                (0, 255, 255),
                2
            )

            cv2.imshow(
                "VisionX - Activity Analysis",
                frame
            )

            # --------------------------------
            # 7. VIDEO PLAYBACK
            # --------------------------------

            if is_video:

                for _ in range(FRAME_STRIDE - 1):

                    if not cap.grab():
                        break

                elapsed = (
                    time.monotonic() - iteration_start
                )

                remaining = playback_interval - elapsed

                delay = max(
                    1,
                    int(remaining * 1000)
                )

            else:

                delay = 1

            if cv2.waitKey(delay) & 0xFF == ord("q"):
                break

    finally:

        cap.release()
        pose_detector.close()
        cv2.destroyAllWindows()

        print("\nVisionX stopped.")


if __name__ == "__main__":
    main()
