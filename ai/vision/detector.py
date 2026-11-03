from dataclasses import dataclass


@dataclass
class Detection:
    label: str
    confidence: float
    box: tuple[int, int, int, int]  # left, top, right, bottom


class YoloDetector:
    """Finds chosen kinds of things in a picture with a YOLO model."""

    def __init__(self, model_path: str, labels: set[str], min_confidence: float):
        from ultralytics import YOLO  # imported here so the tests do not need the heavy package

        self.model = YOLO(model_path)
        self.names = self.model.names
        self.labels = {name.lower() for name in labels}
        self.min_confidence = min_confidence

    def detect(self, frame) -> list[Detection]:
        result = self.model(frame, verbose=False, conf=self.min_confidence)[0]
        found = []
        for box in result.boxes:
            name = str(self.names[int(box.cls[0])]).lower()
            if name in self.labels:
                left, top, right, bottom = (int(v) for v in box.xyxy[0].tolist())
                found.append(Detection(name, float(box.conf[0]), (left, top, right, bottom)))
        return found
