
import sys
from pathlib import Path
from collections import defaultdict
from statistics import median
import cv2
import numpy as np

ML2_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ML2_DIR))

from tracking.tracker import PersonTracker
from pose.pose_detector import PoseDetector


VIDEO_DIR = ML2_DIR / "activity" / "videos"
FRAME_STRIDE = 4

VIDEOS = [
    ("walking", "abhwalk.mp4"),
    ("walking", "irswalk.mp4"),
    ("walking", "jithwalk.mp4"),
    ("running", "abirun.mp4"),
    ("running", "irsrun.mp4"),
    ("running", "jitrun.mp4"),
]


def distance(a, b):
    return np.sqrt(
        (a[0] - b[0]) ** 2 +
        (a[1] - b[1]) ** 2
    )


def percentile(values, p):
    return float(np.percentile(values, p))


def analyze_video(tracker, pose_detector, activity, filename):
    video_path = VIDEO_DIR / activity / filename

    if not video_path.exists():
        print(f"\nMISSING VIDEO: {video_path}")
        return

    print("\n" + "=" * 60)
    print(f"VIDEO: {filename}")
    print(f"ACTUAL ACTIVITY: {activity.upper()}")
    print("=" * 60)

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print("ERROR: Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)

    if not fps or fps <= 0 or fps > 120:
        fps = 30.0

    previous = {}
    measurements = defaultdict(list)
    valid_poses = defaultdict(int)

    frame_index = 0

    while True:
        success, frame = cap.read()

        if not success:
            break

        timestamp = frame_index / fps

        people = tracker.detect(frame)

        height, width = frame.shape[:2]

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
            pose = pose_detector.detect(crop)

            if pose is None:
                continue

            valid_poses[track_id] += 1

            current = {
                "time": timestamp,
                "left": pose["left_ankle"],
                "right": pose["right_ankle"]
            }

            if track_id in previous:
                old = previous[track_id]
                dt = timestamp - old["time"]

                if dt > 0:
                    left_speed = (
                        distance(old["left"], current["left"]) / dt
                    )

                    right_speed = (
                        distance(old["right"], current["right"]) / dt
                    )

                    movement = (left_speed + right_speed) / 2.0
                    measurements[track_id].append(movement)

            previous[track_id] = current

        frame_index += 1

        for _ in range(FRAME_STRIDE - 1):
            if not cap.grab():
                break
            frame_index += 1

    cap.release()

    if not measurements:
        print("NO VALID MOVEMENT MEASUREMENTS.")
        print("Check person detection and pose visibility.")
        return

    print(f"Source FPS: {fps:.2f}")
    print(f"Frames sampled: {len(measurements)} track(s)")

    for track_id, values in measurements.items():
        if not values:
            continue

        print(f"\nTRACK ID: {track_id}")
        print(f"Valid pose frames: {valid_poses[track_id]}")
        print(f"Movement samples: {len(values)}")
        print(f"Median: {median(values):.5f}")
        print(f"P75:    {percentile(values, 75):.5f}")
        print(f"P90:    {percentile(values, 90):.5f}")
        print(f"Maximum:{max(values):.5f}")

    print("\nNOTE: These values use the current crop-relative")
    print("ankle measurement. They are for diagnosis, not")
    print("validated real-world walking/running speeds.")


def main():
    print("=" * 60)
    print("       VISIONX MOVEMENT CALIBRATION")
    print("=" * 60)

    print("\nInitializing MediaPipe...")
    pose_detector = PoseDetector()

    try:
        for activity, filename in VIDEOS:
            print("\nInitializing YOLO for", filename)
            tracker = PersonTracker()

            analyze_video(
                tracker,
                pose_detector,
                activity,
                filename
            )

            # Release this video's model before the next one.
            del tracker

    finally:
        pose_detector.close()

    print("\n" + "=" * 60)
    print("CALIBRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
