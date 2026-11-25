
from collections import defaultdict, deque
from statistics import median
import math


class MovementAnalyzer:
    def __init__(self):
        self.history = defaultdict(lambda: deque(maxlen=50))
        self.decisions = defaultdict(lambda: deque(maxlen=5))

        self.UNKNOWN_MAX = 0.20
        self.RUN_THRESHOLD = 0.72

        self.WINDOW_SECONDS = 1.5
        self.MAX_HISTORY_SECONDS = 2.5

    @staticmethod
    def distance(a, b):
        return math.sqrt(
            (a[0] - b[0]) ** 2 +
            (a[1] - b[1]) ** 2
        )

    def update(self, track_id, pose, timestamp,
               face_detected=None):

        if pose is None:
            return "UNKNOWN", {
                "score": 0,
                "speed": 0.0,
                "confidence": 0
            }

        history = self.history[track_id]

        history.append({
            "time": timestamp,
            "left": pose["left_ankle"],
            "right": pose["right_ankle"]
        })

        while (
            history and
            timestamp - history[0]["time"] >
            self.MAX_HISTORY_SECONDS
        ):
            history.popleft()

        if len(history) < 5:
            return "UNKNOWN", {
                "score": 0,
                "speed": 0.0,
                "confidence": 0
            }

        if timestamp - history[0]["time"] < self.WINDOW_SECONDS:
            return "UNKNOWN", {
                "score": 0,
                "speed": 0.0,
                "confidence": 0
            }

        samples = list(history)
        speeds = []

        for previous, current in zip(
            samples[:-1], samples[1:]
        ):
            dt = current["time"] - previous["time"]

            if dt <= 0:
                continue

            left_speed = (
                self.distance(
                    previous["left"],
                    current["left"]
                ) / dt
            )

            right_speed = (
                self.distance(
                    previous["right"],
                    current["right"]
                ) / dt
            )

            speeds.append(
                (left_speed + right_speed) / 2.0
            )

        if len(speeds) < 4:
            return "UNKNOWN", {
                "score": 0,
                "speed": 0.0,
                "confidence": 0
            }

        movement_speed = median(speeds)

        if movement_speed < self.UNKNOWN_MAX:
            candidate = "UNKNOWN"

        elif movement_speed < self.RUN_THRESHOLD:
            candidate = "WALKING"

        else:
            candidate = "RUNNING"

        decisions = self.decisions[track_id]
        decisions.append(candidate)

        walking_count = decisions.count("WALKING")
        running_count = decisions.count("RUNNING")
        unknown_count = decisions.count("UNKNOWN")

        if unknown_count >= 3:
            activity = "UNKNOWN"
        elif running_count >= 3:
            activity = "RUNNING"
        elif walking_count >= 3:
            activity = "WALKING"
        else:
            activity = "UNKNOWN"

        # Temporary activity rating
        if activity == "WALKING":
            score = 40 if face_detected is False else 10

        elif activity == "RUNNING":
            score = 30

        else:
            score = 0

        confidence = round(
            max(
                walking_count,
                running_count,
                unknown_count
            ) / len(decisions) * 100
        )

        return activity, {
            "speed": round(movement_speed, 3),
            "score": score,
            "confidence": confidence
        }

    def remove_track(self, track_id):
        self.history.pop(track_id, None)
        self.decisions.pop(track_id, None)
