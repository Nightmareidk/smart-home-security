"""Add, list and delete the people the house recognises.

    python enrol.py add sara --source 0              take 6 photos from the webcam
    python enrol.py add sara --images a.jpg b.jpg    use pictures instead
    python enrol.py add sara --source 0 --can-unlock  also allow this person to open the door by face
    python enrol.py list
    python enrol.py delete sara

Faces are only saved with the person's clear consent. Only numbers describing the face are kept,
on this computer, in ai/face/data/. Nothing is uploaded.
"""
import argparse
import sys
import time
from datetime import datetime

from store import FaceStore, clean_name

CONSENT = (
    "\nCONSENT\n"
    "  This will save numbers that describe {name}'s face on THIS computer only (not the photos).\n"
    "  They are used so the house can recognise {name}{unlock}.\n"
    "  {name} can ask to be deleted at any time:  python enrol.py delete {name}\n"
)


def grab_from_camera(engine, source: str, count: int, min_score: float):
    import cv2

    cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
    if not cap.isOpened():
        raise SystemExit("Could not open the camera.")
    print(f"Look at the camera. Taking {count} photos, one every second. Turn your head a little between photos.")
    samples, last = [], 0.0
    deadline = time.time() + 60
    while len(samples) < count and time.time() < deadline:
        ok, frame = cap.read()
        if not ok:
            continue
        faces = engine.detect(frame)
        if len(faces) == 1 and faces[0][-1] >= min_score and time.time() - last >= 1.0:
            samples.append(engine.embed(frame, faces[0]))
            last = time.time()
            print(f"  photo {len(samples)} of {count}")
    cap.release()
    return samples


def grab_from_images(engine, paths):
    import cv2

    samples = []
    for path in paths:
        frame = cv2.imread(path)
        if frame is None:
            print(f"  {path}: could not read it")
            continue
        faces = engine.detect(frame)
        if len(faces) != 1:
            print(f"  {path}: needs exactly one face, found {len(faces)}")
            continue
        samples.append(engine.embed(frame, faces[0]))
        print(f"  {path}: ok")
    return samples


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("name")
    a.add_argument("--source", default=None, help="webcam number (default 0 when no --images)")
    a.add_argument("--images", nargs="*")
    a.add_argument("--photos", type=int, default=6)
    a.add_argument("--can-unlock", action="store_true", help="allow this person to open the door by face")
    a.add_argument("--yes", action="store_true", help="I already have this person's written consent (skips the question)")
    sub.add_parser("list")
    d = sub.add_parser("delete")
    d.add_argument("name")
    args = p.parse_args()

    store = FaceStore()
    if args.cmd == "list":
        names = store.names()
        print("\n".join(f"{n}{'  (can open the door)' if store.can_unlock(n) else ''}" for n in names) or "Nobody is enrolled yet.")
        return
    if args.cmd == "delete":
        print("Deleted." if store.delete(args.name) else "Nobody with that name.")
        return

    name = clean_name(args.name)
    print(CONSENT.format(name=name, unlock=" and open the door for them" if args.can_unlock else ""))
    if not args.yes:
        if input(f"Does {name} agree, and is the consent written down? Type yes: ").strip().lower() != "yes":
            raise SystemExit("Nothing saved.")
    from engine import FaceEngine

    engine = FaceEngine()
    samples = grab_from_images(engine, args.images) if args.images else grab_from_camera(engine, args.source or "0", args.photos, 0.9)
    if len(samples) < 3:
        raise SystemExit(f"Only {len(samples)} usable photo(s). Need at least 3. Nothing saved.")
    consent = f"consent confirmed {datetime.now().isoformat(timespec='seconds')}"
    store.add(name, samples, can_unlock=args.can_unlock, consent=consent)
    print(f"Saved {len(samples)} samples for {name}.")


if __name__ == "__main__":
    sys.exit(main())
