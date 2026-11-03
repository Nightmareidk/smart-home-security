"""Face recognition: tells the house who is at the camera.

    python main.py --source 0 --show                       laptop webcam with a preview
    python main.py --source http://<camera-ip>/stream      the ESP32-CAM
    python main.py --source clip.mp4 --dry-run             a video: print only, send nothing
    python main.py --source 0 --allow-unlock               also let enrolled people open the door by face

Known faces are reported with their name (they show as Home in the app). Unknown faces are reported with no name
(an alert if the system is armed). Opening the door needs --allow-unlock, a person enrolled with --can-unlock,
a strict match, and several matches in a row. Remember that a simple face system can be fooled by a photo.
"""
import argparse
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from confirm import Confirmer
from matcher import identify
from store import FaceStore

log = logging.getLogger("face")


def open_door(server: str, token: str, name: str) -> bool:
    body = json.dumps({"action": "unlock", "source": "face", "user": name}).encode()
    req = urllib.request.Request(
        f"{server.rstrip('/')}/api/door",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            return True
    except (urllib.error.URLError, TimeoutError) as e:
        log.warning("Could not ask the server to open the door: %s", e)
        return False


def draw(frame, faces, labels):
    import cv2

    for row, (name, score) in zip(faces, labels):
        x, y, w, h = (int(v) for v in row[:4])
        color = (0, 200, 120) if name else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, f"{name or 'unknown'} {score:.2f}", (x, max(18, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return frame


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", default="0")
    p.add_argument("--host", default="localhost", help="message broker address")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--server", default="http://localhost:8000", help="house server (used only for opening the door)")
    p.add_argument("--token", default=os.environ.get("HOME_API_TOKEN", ""))
    p.add_argument("--match", type=float, default=0.45, help="how alike a face must be to be named (0 to 1)")
    p.add_argument("--unlock-match", type=float, default=0.6, help="how alike a face must be to open the door")
    p.add_argument("--allow-unlock", action="store_true", help="let enrolled people open the door by face")
    p.add_argument("--frames", type=int, default=3, help="pictures in a row needed before reporting")
    p.add_argument("--cooldown", type=float, default=5.0)
    p.add_argument("--every", type=int, default=2)
    p.add_argument("--show", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    import cv2

    from engine import FaceEngine
    from publisher import EventPublisher

    store = FaceStore()
    people = store.people()
    if not people:
        raise SystemExit("Nobody is enrolled yet. Add someone first:  python enrol.py add NAME")
    if args.allow_unlock and not args.token:
        raise SystemExit("Opening the door needs the server token: set HOME_API_TOKEN or use --token.")
    engine = FaceEngine()
    publisher = None if args.dry_run else EventPublisher(args.host, args.port)
    if publisher:
        publisher.wait_until_connected()
    gates: dict[str, Confirmer] = {}
    unlock_gates: dict[str, Confirmer] = {}
    cap = cv2.VideoCapture(int(args.source) if re.fullmatch(r"\d+", args.source) else args.source)
    is_file = not re.fullmatch(r"\d+", args.source) and Path(args.source).exists()
    count = failures = 0
    log.info("Watching. Enrolled: %s. Door opening by face is %s.", ", ".join(sorted(people)), "ON" if args.allow_unlock else "off")

    def say(event: dict):
        sent = "printed only" if publisher is None else ("sent" if publisher.publish(event) else "NOT sent")
        log.info("%s (%s)", event, sent)

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                if is_file:
                    break
                failures += 1
                if failures >= 30:
                    cap.release()
                    time.sleep(2)
                    cap = cv2.VideoCapture(int(args.source) if re.fullmatch(r"\d+", args.source) else args.source)
                    failures = 0
                time.sleep(0.1)
                continue
            failures = 0
            count += 1
            if count % args.every:
                continue
            now = time.time()
            faces = engine.detect(frame)
            labels = []
            seen = set()
            for row in faces:
                name, score = identify(engine.embed(frame, row), people, args.match)
                labels.append((name, score))
                key = name or "?"
                seen.add(key)
                gate = gates.setdefault(key, Confirmer(args.frames, args.cooldown))
                if gate.update(True, now):
                    event = {"type": "face", "confidence": round(score if name else float(row[-1]), 2)}
                    if name:
                        event["name"] = name
                    say(event)
                if args.allow_unlock and name and store.can_unlock(name) and score >= args.unlock_match:
                    ug = unlock_gates.setdefault(name, Confirmer(args.frames, 10.0))
                    if ug.update(True, now):
                        log.info("Opening the door for %s (match %.2f)", name, score)
                        open_door(args.server, args.token, name)
            for key in list(gates):
                if key not in seen:
                    gates[key].update(False, now)
            for key in list(unlock_gates):
                if key not in seen:
                    unlock_gates[key].update(False, now)
            if args.show:
                cv2.imshow("Face recognition (press q to stop)", draw(frame.copy(), faces, labels))
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


if __name__ == "__main__":
    main()
