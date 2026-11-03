from pathlib import Path

import numpy as np

MODELS = Path(__file__).resolve().parent / "models"
DETECTOR = MODELS / "face_detection_yunet_2023mar.onnx"
RECOGNISER = MODELS / "face_recognition_sface_2021dec.onnx"


class FaceEngine:
    """Finds faces in a picture (YuNet) and turns each into 128 numbers (SFace). Both run inside OpenCV."""

    def __init__(self, min_score: float = 0.85):
        import cv2

        for path in (DETECTOR, RECOGNISER):
            if not path.exists():
                raise SystemExit(f"Missing model file: {path.name}. Run:  python get_models.py")
        self.cv2 = cv2
        self.detector = cv2.FaceDetectorYN.create(str(DETECTOR), "", (320, 320), min_score, 0.3, 5000)
        self.recogniser = cv2.FaceRecognizerSF.create(str(RECOGNISER), "")

    def detect(self, frame) -> np.ndarray:
        """Returns one row per face: x, y, width, height, 10 landmark numbers, score."""
        h, w = frame.shape[:2]
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(frame)
        return faces if faces is not None else np.empty((0, 15), dtype=np.float32)

    def embed(self, frame, face_row) -> np.ndarray:
        aligned = self.recogniser.alignCrop(frame, face_row)
        return self.recogniser.feature(aligned).ravel()
