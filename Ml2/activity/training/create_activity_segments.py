
from pathlib import Path
import csv
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = PROJECT_ROOT / "Ml2" / "activity" / "dataset"
OUTPUT_FILE = (
    PROJECT_ROOT
    / "Ml2"
    / "activity"
    / "annotations"
    / "activity_segments.csv"
)


def get_video_duration(npz_path):
    with np.load(npz_path, allow_pickle=False) as data:
        timestamps = data["timestamps"]
        sample_fps = float(data["sample_fps"].item())

    if len(timestamps) == 0 or sample_fps <= 0:
        raise ValueError(f"Invalid timing data: {npz_path}")

    return float(timestamps.max()) + (1.0 / sample_fps)


def main():
    segments = []

    # Walking and running examples
    for label in ["walking", "running"]:
        folder = DATASET_ROOT / label

        for path in sorted(folder.glob("*.npz")):
            duration = get_video_duration(path)

            segments.append({
                "video_name": path.stem,
                "start_seconds": 0.0,
                "end_seconds": round(duration, 3),
                "label": label
            })

    # Fighting video: walking first, fighting from 2 seconds
    fight_path = DATASET_ROOT / "fighting" / "fight1.npz"

    if fight_path.exists():
        duration = get_video_duration(fight_path)

        segments.extend([
            {
                "video_name": "fight1",
                "start_seconds": 0.0,
                "end_seconds": 2.0,
                "label": "walking"
            },
            {
                "video_name": "fight1",
                "start_seconds": 2.0,
                "end_seconds": round(duration, 3),
                "label": "fighting"
            }
        ])

    # Violence video: violence from the beginning
    violence_path = DATASET_ROOT / "violence" / "voilance.npz"

    if violence_path.exists():
        duration = get_video_duration(violence_path)

        segments.append({
            "video_name": "voilance",
            "start_seconds": 0.0,
            "end_seconds": round(duration, 3),
            "label": "violence"
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "video_name",
                "start_seconds",
                "end_seconds",
                "label"
            ]
        )

        writer.writeheader()
        writer.writerows(segments)

    print("=" * 60)
    print("VISIONX ACTIVITY ANNOTATIONS")
    print("=" * 60)

    for segment in segments:
        print(
            f"{segment['video_name']:<12} "
            f"{segment['start_seconds']:>6.2f}s - "
            f"{segment['end_seconds']:>6.2f}s  "
            f"{segment['label'].upper()}"
        )

    print(f"\nSaved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
