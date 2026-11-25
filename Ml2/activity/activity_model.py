
from collections import deque
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


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
        return self.classifier(output[:, -1, :])


class ActivityModel:
    def __init__(self):
        base_dir = Path(__file__).resolve().parent
        model_path = base_dir / "models" / "activity_lstm.pth"

        if not model_path.exists():
            raise FileNotFoundError(
                f"Trained model not found: {model_path}"
            )

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        checkpoint = torch.load(
            model_path,
            map_location=self.device,
            weights_only=False
        )

        self.classes = checkpoint["classes"]
        self.input_size = checkpoint["input_size"]
        self.window_size = checkpoint["window_size"]

        self.model = ActivityLSTM(
            input_size=self.input_size,
            num_classes=len(self.classes)
        ).to(self.device)

        self.model.load_state_dict(
            checkpoint["model_state_dict"]
        )

        self.model.eval()

        self.sequence = deque(maxlen=self.window_size)
        self.last_timestamp = None

        self.confidence_threshold = 0.60
        self.max_gap = 0.15

        print("Activity LSTM loaded")
        print("Activity device:", self.device)
        print("Classes:", self.classes)
        print("Window size:", self.window_size)

    def reset(self):
        self.sequence.clear()
        self.last_timestamp = None

    def update(self, features, timestamp):
        if features is None:
            return "UNKNOWN", 0.0

        features = np.asarray(
            features,
            dtype=np.float32
        ).reshape(-1)

        if features.size != self.input_size:
            raise ValueError(
                f"Expected {self.input_size} features, "
                f"received {features.size}"
            )

        if not np.isfinite(features).all():
            return "UNKNOWN", 0.0

        if (
            self.last_timestamp is not None
            and timestamp - self.last_timestamp > self.max_gap
        ):
            self.sequence.clear()

        self.last_timestamp = timestamp
        self.sequence.append(features)

        if len(self.sequence) < self.window_size:
            return "UNKNOWN", 0.0

        sequence = np.asarray(
            self.sequence,
            dtype=np.float32
        )

        tensor = torch.from_numpy(
            sequence
        ).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probabilities = torch.softmax(logits, dim=1)

        confidence, predicted_index = probabilities.max(dim=1)

        confidence = float(confidence.item())
        activity = self.classes[int(predicted_index.item())]

        if confidence < self.confidence_threshold:
            return "UNKNOWN", confidence

        return activity.upper(), confidence

    def close(self):
        self.reset()
