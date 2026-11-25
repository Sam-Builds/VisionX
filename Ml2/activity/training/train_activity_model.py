
from pathlib import Path
import csv
import json

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


# --------------------------------------------------
# PATHS AND CONFIGURATION
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]

DATASET_DIR = ROOT / "Ml2" / "activity" / "dataset"
ANNOTATION_FILE = (
    ROOT / "Ml2" / "activity" / "annotations"
    / "activity_segments.csv"
)

MODEL_DIR = ROOT / "Ml2" / "activity" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "activity_lstm.pth"
DATASET_PATH = MODEL_DIR / "training_sequences.npz"

CLASSES = [
    "walking",
    "running",
    "fighting",
    "violence"
]

NUM_PEOPLE = 2
WINDOW_SIZE = 23
STRIDE = 8

BATCH_SIZE = 8
EPOCHS = 80
LEARNING_RATE = 0.001

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# --------------------------------------------------
# MODEL
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
# LOAD ANNOTATIONS
# --------------------------------------------------

def load_annotations():

    annotations = {}

    with open(
        ANNOTATION_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            video = row["video_name"]

            annotations.setdefault(video, []).append({
                "start": float(row["start_seconds"]),
                "end": float(row["end_seconds"]),
                "label": row["label"].lower()
            })

    return annotations


# --------------------------------------------------
# LOAD VIDEO AND BUILD FRAME FEATURES
# --------------------------------------------------

def load_video_frames(path):

    with np.load(path, allow_pickle=False) as data:

        poses = data["poses"]
        track_ids = data["track_ids"]
        timestamps = data["timestamps"]
        frame_indices = data["frame_indices"]

    if len(poses) == 0:
        return [], []

    # Select the two longest tracks.
    unique_ids, counts = np.unique(
        track_ids,
        return_counts=True
    )

    selected_ids = unique_ids[
        np.argsort(counts)[::-1][:NUM_PEOPLE]
    ]

    frames = {}

    for pose, track_id, timestamp, frame_index in zip(
        poses,
        track_ids,
        timestamps,
        frame_indices
    ):

        if track_id not in selected_ids:
            continue

        frame_index = int(frame_index)

        if frame_index not in frames:
            frames[frame_index] = {
                "time": float(timestamp),
                "people": {}
            }

        person_slot = int(
            np.where(selected_ids == track_id)[0][0]
        )

        frames[frame_index]["people"][person_slot] = pose

    frame_features = []
    frame_times = []

    for frame_index in sorted(frames):

        frame = frames[frame_index]

        people_features = []

        for person_slot in range(NUM_PEOPLE):

            pose = frame["people"].get(person_slot)

            if pose is None:
                pose = np.zeros((33, 4), dtype=np.float32)

            people_features.append(pose.reshape(-1))

        combined = np.concatenate(people_features)

        frame_features.append(combined)
        frame_times.append(frame["time"])

    return frame_features, frame_times


# --------------------------------------------------
# CREATE LABELED WINDOWS
# --------------------------------------------------

def create_training_data():

    annotations = load_annotations()

    all_sequences = []
    all_labels = []

    print("\nCreating temporal sequences...")

    for class_name in CLASSES:

        folder = DATASET_DIR / class_name

        if not folder.exists():
            continue

        for path in sorted(folder.glob("*.npz")):

            video_name = path.stem

            if video_name not in annotations:
                print("Missing annotation:", video_name)
                continue

            features, times = load_video_frames(path)

            if len(features) < WINDOW_SIZE:
                print("Too few frames:", video_name)
                continue

            features = np.asarray(
                features,
                dtype=np.float32
            )

            times = np.asarray(times, dtype=np.float32)

            video_count = 0

            for start in range(
                0,
                len(features) - WINDOW_SIZE + 1,
                STRIDE
            ):

                end = start + WINDOW_SIZE

                window_times = times[start:end]

                # Reject windows with large timestamp gaps.
                if np.max(np.diff(window_times)) > 0.15:
                    continue

                window_start = float(window_times[0])
                window_end = float(window_times[-1])

                # Only accept windows fully inside one annotation.
                matching_label = None

                for segment in annotations[video_name]:

                    if (
                        window_start >= segment["start"]
                        and window_end < segment["end"]
                    ):
                        matching_label = segment["label"]
                        break

                if matching_label not in CLASSES:
                    continue

                sequence = features[start:end]

                all_sequences.append(sequence)
                all_labels.append(
                    CLASSES.index(matching_label)
                )

                video_count += 1

            print(
                f"{video_name}: "
                f"{video_count} sequences"
            )

    if not all_sequences:
        raise RuntimeError(
            "No training sequences generated. "
            "Check annotations and dataset paths."
        )

    X = np.asarray(all_sequences, dtype=np.float32)
    y = np.asarray(all_labels, dtype=np.int64)

    return X, y


# --------------------------------------------------
# TRAIN
# --------------------------------------------------

def train():

    print("=" * 60)
    print("             VISIONX ACTIVITY TRAINING")
    print("=" * 60)

    print("Device:", DEVICE)

    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))

    X, y = create_training_data()

    print("\nDataset shape:", X.shape)
    print("Labels shape:", y.shape)

    print("\nClass distribution:")

    for index, name in enumerate(CLASSES):
        print(
            f"{name.upper()}:",
            int(np.sum(y == index))
        )

    # Save generated sequences for inspection/reuse.
    np.savez_compressed(
        DATASET_PATH,
        X=X,
        y=y,
        classes=np.asarray(CLASSES)
    )

    X_tensor = torch.tensor(X, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.long)

    loader = DataLoader(
        TensorDataset(X_tensor, y_tensor),
        batch_size=BATCH_SIZE,
        shuffle=True
    )

    input_size = X.shape[2]

    model = ActivityLSTM(
        input_size=input_size,
        num_classes=len(CLASSES)
    ).to(DEVICE)

    # Balance the contribution of each class.
    class_counts = np.bincount(
        y,
        minlength=len(CLASSES)
    )

    class_weights = len(y) / (
        len(CLASSES) * np.maximum(class_counts, 1)
    )

    weights_tensor = torch.tensor(
        class_weights,
        dtype=torch.float32,
        device=DEVICE
    )

    criterion = nn.CrossEntropyLoss(
        weight=weights_tensor
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE
    )

    print("\nStarting training...\n")

    for epoch in range(EPOCHS):

        model.train()

        total_loss = 0.0
        correct = 0
        total = 0

        for batch_X, batch_y in loader:

            batch_X = batch_X.to(DEVICE)
            batch_y = batch_y.to(DEVICE)

            optimizer.zero_grad()

            outputs = model(batch_X)

            loss = criterion(outputs, batch_y)

            loss.backward()

            optimizer.step()

            total_loss += loss.item()

            predictions = outputs.argmax(dim=1)

            correct += (
                predictions == batch_y
            ).sum().item()

            total += batch_y.size(0)

        accuracy = 100.0 * correct / total
        average_loss = total_loss / len(loader)

        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(
                f"Epoch {epoch + 1:03d}/{EPOCHS} | "
                f"Loss: {average_loss:.4f} | "
                f"Training accuracy: {accuracy:.2f}%"
            )

    # Save model and metadata.
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "classes": CLASSES,
            "input_size": input_size,
            "num_people": NUM_PEOPLE,
            "window_size": WINDOW_SIZE,
            "stride": STRIDE
        },
        MODEL_PATH
    )

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

    print("Model saved:", MODEL_PATH)
    print("Sequences saved:", DATASET_PATH)

    print(
        "\nNote: Training accuracy is not real-world "
        "validation accuracy."
    )


if __name__ == "__main__":
    train()
