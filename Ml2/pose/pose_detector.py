
from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class PoseDetector:
    def __init__(self):
        base_dir = Path(__file__).resolve().parents[1]
        model_path = base_dir / "pose" / "pose_landmarker_lite.task"

        if not model_path.exists():
            raise FileNotFoundError(
                f"MediaPipe model not found: {model_path}"
            )

        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(
                model_asset_path=str(model_path)
            ),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.45,
            min_pose_presence_confidence=0.45
        )

        self.landmarker = vision.PoseLandmarker.create_from_options(
            options
        )

        print("MediaPipe Pose initialized")

    def detect(self, person_crop):
        if person_crop is None or person_crop.size == 0:
            return None

        rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.landmarker.detect(mp_image)

        if not result.pose_landmarks:
            return None

        landmarks = result.pose_landmarks[0]

        # Each landmark contains normalized x, y, z and visibility.
        # Shape: (33, 4)
        landmark_array = np.array(
            [
                [
                    point.x,
                    point.y,
                    point.z,
                    getattr(point, "visibility", 0.0)
                ]
                for point in landmarks
            ],
            dtype=np.float32
        )

        left_hip = landmarks[23]
        right_hip = landmarks[24]
        left_ankle = landmarks[27]
        right_ankle = landmarks[28]

        return {
            "landmarks": landmark_array,

            # Keep these fields for the existing movement analyzer.
            "left_ankle": (
                left_ankle.x,
                left_ankle.y
            ),
            "right_ankle": (
                right_ankle.x,
                right_ankle.y
            ),
            "hip_y": (
                left_hip.y + right_hip.y
            ) / 2.0
        }

    def close(self):
        self.landmarker.close()
