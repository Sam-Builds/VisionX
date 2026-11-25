
import cv2
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VIDEO_ROOT = PROJECT_ROOT / "Ml2" / "activity" / "videos"

CLASSES = [
    "walking",
    "running",
    "fighting",
    "voilance"
]


def inspect_video(video_path):
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print(f"ERROR: Cannot open {video_path.name}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    duration = frames / fps if fps > 0 else 0

    print(f"\nVideo: {video_path.name}")
    print(f"FPS: {fps:.2f}")
    print(f"Frames: {frames}")
    print(f"Resolution: {width}x{height}")
    print(f"Duration: {duration:.2f} seconds")

    cap.release()


def main():
    print("=" * 55)
    print("          VISIONX VIDEO DATASET INSPECTOR")
    print("=" * 55)

    for class_name in CLASSES:
        folder = VIDEO_ROOT / class_name

        print(f"\n--- {class_name.upper()} ---")

        if not folder.exists():
            print("Folder not found.")
            continue

        videos = list(folder.glob("*.mp4"))

        if not videos:
            print("No MP4 videos found.")
            continue

        for video_path in videos:
            inspect_video(video_path)

    print("\nInspection complete.")


if __name__ == "__main__":
    main()
