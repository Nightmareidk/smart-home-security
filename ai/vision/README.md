# Camera AI

Watches a camera picture and tells the house when it sees a **person** (and, with a fire model, **fire or smoke**).
It sends `home/camera/event` messages to the broker (see `docs/CONTRACT.md`). The server decides if it is an alert.

## Set up (once)

```bash
cd ai/vision
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

The first run downloads the small YOLO model (`yolov8n.pt`, about 6 MB).

## Try it

```bash
.venv\Scripts\python main.py --image photo.jpg                       look at one picture
.venv\Scripts\python main.py --source 0 --show --dry-run             laptop webcam, preview, send nothing
.venv\Scripts\python main.py --source 0                              laptop webcam, send events to the house
.venv\Scripts\python main.py --source http://<camera-ip>/stream      the ESP32-CAM (when it is ready)
```

Arm the system in the app, walk in front of the camera, and an intruder alert appears.

## How it avoids false alarms

- A person must be seen in **3 pictures in a row** (`--frames`) with confidence **0.6 or more** (`--confidence`).
- After reporting, it waits **5 seconds** (`--cooldown`) before reporting the same sighting again.
- It looks at every 2nd picture (`--every`) to save work.

## Fire and smoke

Give it a YOLO model trained for fire and smoke with `--fire-model path\to\model.pt`. Without one, only people are detected.
Test only with a small supervised candle, or a fire video on a screen.

## Files

| File | What it does |
|---|---|
| `main.py` | The program: reads pictures, detects, reports |
| `detector.py` | Wraps the YOLO model |
| `confirm.py` | "Seen in several pictures in a row" logic (tested) |
| `publisher.py` | Sends events to the broker |
| `tests/` | `python -m pytest tests` |
