
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = PROJECT_ROOT / "Ml2" / "activity" / "dataset"

CLASSES = ["walking", "running", "fighting", "violence"]


def inspect_file(path):
    print("\n" + "-" * 65)
    print(f"FILE: {path.name}")

    with np.load(path, allow_pickle=False) as data:
        for key in data.files:
            array = data[key]
            print(f"{key}: shape={array.shape}, dtype={array.dtype}")

        pose_key = next(
            (
                key for key in data.files
                if data[key].ndim == 3
                and data[key].shape[1:] == (33, 4)
            ),
            None
        )

        if pose_key is None:
            print("Pose array not found.")
            return

        poses = data[pose_key]

        finite_ratio = np.isfinite(poses).mean() * 100
        visibility = poses[:, :, 3]

        print(f"\nPose finite values: {finite_ratio:.2f}%")
        print(
            "Average landmark visibility:",
            f"{np.nanmean(visibility):.3f}"
        )
        print(
            "Landmarks with visibility >= 0.5:",
            f"{(visibility >= 0.5).mean() * 100:.2f}%"
        )

        print(
            "Pose values within normalized XY range:",
            f"{((poses[:, :, :2] >= 0) & (poses[:, :, :2] <= 1)).mean() * 100:.2f}%"
        )


def main():
    print("=" * 65)
    print("          VISIONX POSE QUALITY INSPECTOR")
    print("=" * 65)

    for class_name in CLASSES:
        folder = DATASET_ROOT / class_name

        print(f"\n========== {class_name.upper()} ==========")

        if not folder.exists():
            print("Folder not found.")
            continue

        files = sorted(folder.glob("*.npz"))

        if not files:
            print("No NPZ files found.")
            continue

        for path in files:
            inspect_file(path)

    print("\nPose quality inspection complete.")


if __name__ == "__main__":
    main()
