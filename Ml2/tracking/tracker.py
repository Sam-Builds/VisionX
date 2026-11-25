
from pathlib import Path

import torch
from ultralytics import YOLO


class PersonTracker:
    def __init__(self):
        self.use_gpu = torch.cuda.is_available()
        self.device = 0 if self.use_gpu else "cpu"

        base_dir = Path(__file__).resolve().parents[1]
        model_path = base_dir / "models" / "yolo11n.pt"

        self.model = YOLO(
            str(model_path) if model_path.exists()
            else "yolo11n.pt"
        )

        print(f"YOLO device: {self.device}")
        print("YOLO optimized for faster inference")

    def detect(self, frame):
        results = self.model.track(
            source=frame,
            persist=True,
            tracker="bytetrack.yaml",
            classes=[0],
            conf=0.35,
            imgsz=416,
            device=self.device,
            half=self.use_gpu,
            verbose=False
        )

        people = []

        if not results:
            return people

        boxes = results[0].boxes

        if boxes is None or boxes.id is None:
            return people

        coordinates = boxes.xyxy.cpu().numpy()
        track_ids = boxes.id.int().cpu().tolist()

        for box, track_id in zip(coordinates, track_ids):
            x1, y1, x2, y2 = map(int, box)

            people.append({
                "id": int(track_id),
                "bbox": (x1, y1, x2, y2)
            })

        return people
