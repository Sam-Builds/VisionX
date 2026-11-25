
from pathlib import Path
from collections import Counter

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = PROJECT_ROOT / "Ml2" / "activity" / "dataset"

CLASSES = [
    "walking",
    "running",
    "fighting",
    "violence"
]


def inspect_file(path, expected_label):
    print("\n" + "-" * 65)
    print(f"FILE: {path.name}")

    try:
        with np.load(path, allow_pickle=False) as data:
            poses = data["poses"]
            track_ids = data["track_ids"]
            timestamps = data["timestamps"]
            frame_indices = data["frame_indices"]
            label = str(data["label"].item())

    except Exception as error:
        print(f"ERROR: Could not read file: {error}")
        return

    print(f"Label: {label}")
    print(f"Pose shape: {poses.shape}")
    print(f"Track ID shape: {track_ids.shape}")
    print(f"Timestamp shape: {timestamps.shape}")

    valid = (
        poses.ndim == 3
        and poses.shape[1:] == (33, 4)
        and len(poses) == len(track_ids)
        and len(poses) == len(timestamps)
        and len(poses) == len(frame_indices)
        and np.isfinite(poses).all()
        and np.isfinite(timestamps).all()
    )

    print(f"Data integrity: {'PASS' if valid else 'FAIL'}")

    if not valid:
        return

    if label != expected_label:
        print(f"WARNING: Expected label {expected_label}")

    counts = Counter(track_ids.tolist())

    print(f"Total pose samples: {len(poses)}")
    print(f"Unique track IDs: {len(counts)}")

    print("\nTRACK DETAILS")

    for track_id, count in sorted(counts.items()):
        mask = track_ids == track_id

        track_times = timestamps[mask]
        track_frames = frame_indices[mask]

        order = np.argsort(track_times)
        track_times = track_times[order]
        track_frames = track_frames[order]

        gaps = np.diff(track_times)

        median_gap = (
            float(np.median(gaps))
            if len(gaps) else 0.0
        )

        max_gap = (
            float(np.max(gaps))
            if len(gaps) else 0.0
        )

        print(
            f"ID {track_id}: "
            f"samples={count}, "
            f"time={track_times[0]:.2f}-{track_times[-1]:.2f}s, "
            f"median_gap={median_gap:.3f}s, "
            f"max_gap={max_gap:.3f}s"
        )

    print("\nTimestamp order:", 
          "PASS" if np.all(np.diff(timestamps) >= 0) else
          "INTERLEAVED TRACKS / NOT GLOBALLY ORDERED")

    print("Frame index range:",
          int(frame_indices.min()),
          "to",
          int(frame_indices.max()))


def main():
    print("=" * 65)
    print("           VISIONX DATASET VALIDATOR")
    print("=" * 65)

    for label in CLASSES:
        folder = DATASET_ROOT / label

        print(f"\n\n========== {label.upper()} ==========")

        if not folder.exists():
            print("Folder missing.")
            continue

        files = sorted(folder.glob("*.npz"))

        if not files:
            print("No dataset files found.")
            continue

        for path in files:
            inspect_file(path, label)

    print("\n\nDataset inspection complete.")


if __name__ == "__main__":
    main()
