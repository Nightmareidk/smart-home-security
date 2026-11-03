"""Camera AI: watches a camera picture and reports people (and fire or smoke) to the house.

Examples (run from this folder, inside the vision environment):
    python main.py --source 0 --show                     laptop webcam, with a preview window
    python main.py --source http://<camera-ip>/stream    the ESP32-CAM
    python main.py --source clip.mp4 --dry-run           a video file: print only, send nothing
    python main.py --image photo.jpg                     look at one picture and print what is in it
"""
import argparse
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from confirm import Confirmer

log = logging.getLogger("vision")


def open_source(source: str):
    import cv2

    return cv2.VideoCapture(int(source) if re.fullmatch(r"\d+", source) else source)


def draw(frame, detections, color):
    import cv2

    for d in detections:
        left, top, right, bottom = d.box
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, f"{d.label} {d.confidence:.2f}", (left, max(18, top - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return frame


def save_snapshot(frame, folder: Path) -> str:
    import cv2

    folder.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + ".jpg"
    cv2.imwrite(str(folder / name), frame)
    return name


def look_at_image(args, person, fire):
    import cv2

    frame = cv2.imread(args.image)
    if frame is None:
        raise SystemExit(f"Could not read the picture: {args.image}")
    found = person.detect(frame) + (fire.detect(frame) if fire else [])
    for d in found:
        print(f"{d.label:8} {d.confidence:.2f}  box={d.box}")
    print(f"{len(found)} thing(s) found")
    out = Path(args.snapshots) / ("checked_" + Path(args.image).name)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), draw(frame, found, (0, 200, 120)))
    print(f"Marked picture saved to {out}")


def run(args, person, fire):
    import cv2

    from publisher import EventPublisher

    publisher = None if args.dry_run else EventPublisher(args.host, args.port)
    person_gate = Confirmer(args.frames, args.cooldown)
    fire_gate = Confirmer(args.frames, args.cooldown)
    snapshots = Path(args.snapshots)
    cap = open_source(args.source)
    is_file = not re.fullmatch(r"\d+", args.source) and Path(args.source).exists()
    count = 0
    failures = 0

    def report(kind, detections, frame):
        best = max(d.confidence for d in detections)
        color = (0, 200, 120) if kind == "person" else (0, 0, 255)
        name = save_snapshot(draw(frame.copy(), detections, color), snapshots)
        event = {"type": kind, "confidence": round(best, 2), "snapshot": name}
        sent = "printed only" if publisher is None else ("sent" if publisher.publish(event) else "NOT sent")
        log.info("%s seen (%.2f), %s", kind, best, sent)

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                if is_file:
                    break
                failures += 1
                if failures >= 30:
                    log.warning("No picture from the camera, reconnecting")
                    cap.release()
                    time.sleep(2)
                    cap = open_source(args.source)
                    failures = 0
                time.sleep(0.1)
                continue
            failures = 0
            count += 1
            if count % args.every:
                continue
            now = time.time()
            people = person.detect(frame)
            if person_gate.update(bool(people), now):
                report("person", people, frame)
            hazards = fire.detect(frame) if fire else []
            if fire_gate.update(bool(hazards), now):
                kind = hazards[0].label if hazards[0].label in ("fire", "smoke") else "fire"
                report(kind, hazards, frame)
            if args.show:
                shown = draw(draw(frame.copy(), people, (0, 200, 120)), hazards, (0, 0, 255))
                cv2.imshow("Camera AI (press q to stop)", shown)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        if publisher:
            publisher.close()
        if args.show:
            cv2.destroyAllWindows()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", default="0", help="webcam number, video file, or camera web address")
    p.add_argument("--image", help="look at one picture and exit")
    p.add_argument("--host", default="localhost", help="message broker address")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--model", default="yolov8n.pt", help="YOLO model that knows people (downloaded on first use)")
    p.add_argument("--fire-model", help="optional YOLO model trained for fire and smoke")
    p.add_argument("--confidence", type=float, default=0.6)
    p.add_argument("--frames", type=int, default=3, help="pictures in a row needed before reporting")
    p.add_argument("--cooldown", type=float, default=5.0, help="seconds before reporting the same thing again")
    p.add_argument("--every", type=int, default=2, help="look at every Nth picture (saves work)")
    p.add_argument("--snapshots", default="snapshots")
    p.add_argument("--show", action="store_true", help="show a preview window")
    p.add_argument("--dry-run", action="store_true", help="print events instead of sending them")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    from detector import YoloDetector

    person = YoloDetector(args.model, {"person"}, args.confidence)
    fire = YoloDetector(args.fire_model, {"fire", "smoke"}, args.confidence) if args.fire_model else None
    if args.image:
        look_at_image(args, person, fire)
    else:
        run(args, person, fire)


if __name__ == "__main__":
    main()
