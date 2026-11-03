"""Downloads the two face models (about 37 MB in total) into the models folder.

They come from the OpenCV model zoo (github.com/opencv/opencv_zoo) and are free to use.
"""
import urllib.request
from pathlib import Path

BASE = "https://github.com/opencv/opencv_zoo/raw/main/models"
FILES = {
    "face_detection_yunet_2023mar.onnx": f"{BASE}/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": f"{BASE}/face_recognition_sface/face_recognition_sface_2021dec.onnx",
}
MIN_BYTES = {"face_detection_yunet_2023mar.onnx": 100_000, "face_recognition_sface_2021dec.onnx": 10_000_000}


def main():
    folder = Path(__file__).resolve().parent / "models"
    folder.mkdir(exist_ok=True)
    for name, url in FILES.items():
        target = folder / name
        if target.exists() and target.stat().st_size >= MIN_BYTES[name]:
            print(f"{name}: already there")
            continue
        print(f"{name}: downloading...")
        urllib.request.urlretrieve(url, target)
        if target.stat().st_size < MIN_BYTES[name]:
            target.unlink()
            raise SystemExit(f"{name}: the download looks wrong (too small). Try again.")
        print(f"{name}: done")


if __name__ == "__main__":
    main()
