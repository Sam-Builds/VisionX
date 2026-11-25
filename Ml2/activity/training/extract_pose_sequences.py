
import sys
from pathlib import Path

import cv2
import numpy as np


# Resolve project paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ML2_DIR = PROJECT_ROOT / "Ml2"

sys.path.insert(0, str(ML2_DIR))

from tracking.tracker import PersonTracker
from pose.pose_detector import PoseDetector


VIDEO_ROOT = ML2_DIR / "activity" / "videos"
OUTPUT_ROOT = ML2_DIR / "activity" / "dataset"

# Extract approximately 15 samples per second.
SAMPLE_FPS = 15.0
SAMPLE_INTERVAL = 1.0 / SAMPLE_FPS

CLASSES = {
    "walking": "walking",
    "running": "running",
    "fighting": "fighting",
    "voilance": "violence"
}


def extract_video(video_path, folder_name, label):
    print("\n" + "=" * 55)
    print(f"Processing: {video_path.name}")
    print(f"Label: {label.upper()}")
    print("=" * 55)

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print(f"ERROR: Could not open {video_path}")
        return

    tracker = None
    pose_detector = None

    timestamps = []
    frame_indices = []
    track_ids = []
    pose_sequences = []

    next_sample_time = 0.0
    frame_index = -1

    try:
        # Create fresh tracking state for each video.
        tracker = PersonTracker()
        pose_detector = PoseDetector()

        while True:
            success, frame = cap.read()

            if not success:
                break

            frame_index += 1

            timestamp = (
                cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            )

            # Skip frames until the next sampling time.
            if timestamp + 0.0001 < next_sample_time:
                continue

            next_sample_time += SAMPLE_INTERVAL

            people = tracker.detect(frame)

            height, width = frame.shape[:2]

            for person in people:
                track_id = person["id"]
                x1, y1, x2, y2 = person["bbox"]

                # Keep coordinates inside the frame.
                x1 = max(0, min(x1, width - 1))
                x2 = max(0, min(x2, width))
                y1 = max(0, min(y1, height - 1))
                y2 = max(0, min(y2, height))

                if x2 <= x1 or y2 <= y1:
                    continue

                person_crop = frame[y1:y2, x1:x2]

                pose = pose_detector.detect(person_crop)

                if pose is None:
                    continue

                landmarks = pose["landmarks"]

                if landmarks.shape != (33, 4):
                    continue

                timestamps.append(timestamp)
                frame_indices.append(frame_index)
                track_ids.append(track_id)
                pose_sequences.append(landmarks)

            if frame_index % 60 == 0:
                print(
                    f"Frames processed: {frame_index} | "
                    f"Pose samples: {len(pose_sequences)}"
                )

    except Exception as error:
        print(f"ERROR while processing {video_path.name}: {error}")
        return

    finally:
        cap.release()

        if pose_detector is not None:
            pose_detector.close()

    if not pose_sequences:
        print("WARNING: No pose samples were extracted.")
        return

    output_folder = OUTPUT_ROOT / label
    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = output_folder / f"{video_path.stem}.npz"

    np.savez_compressed(
        output_path,
        poses=np.asarray(pose_sequences, dtype=np.float32),
        track_ids=np.asarray(track_ids, dtype=np.int32),
        timestamps=np.asarray(timestamps, dtype=np.float32),
        frame_indices=np.asarray(frame_indices, dtype=np.int32),
        label=np.asarray(label),
        source_video=np.asarray(video_path.name),
        sample_fps=np.asarray(SAMPLE_FPS, dtype=np.float32)
    )

    unique_tracks = len(set(track_ids))

    print("\nExtraction complete.")
    print(f"Pose samples: {len(pose_sequences)}")
    print(f"Tracked people: {unique_tracks}")
    print(f"Saved to: {output_path}")


def main():
    print("=" * 55)
    print("       VISIONX POSE SEQUENCE EXTRACTOR")
    print("=" * 55)

    for folder_name, label in CLASSES.items():
        class_folder = VIDEO_ROOT / folder_name

        print(f"\n\n--- {label.upper()} ---")

        if not class_folder.exists():
            print(f"Folder not found: {class_folder}")
            continue

        videos = sorted(
            list(class_folder.glob("*.mp4")) +
            list(class_folder.glob("*.avi")) +
            list(class_folder.glob("*.mov"))
        )

        if not videos:
            print("No supported videos found.")
            continue

        for video_path in videos:
            extract_video(video_path, folder_name, label)

    print("\n" + "=" * 55)
    print("POSE EXTRACTION FINISHED")
    print("=" * 55)


if __name__ == "__main__":
    main()
