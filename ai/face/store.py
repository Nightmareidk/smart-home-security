"""Where enrolled faces are kept: one file on this computer, never uploaded.

Only numbers that describe a face are saved (128 of them per photo), not the photos.
The data folder is ignored by git, so faces can never end up on GitHub by accident.
"""
import json
import re
from datetime import datetime
from pathlib import Path

import numpy as np

from matcher import normalise

NAME_RE = re.compile(r"^[a-z0-9_]{1,40}$")
DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "people.json"


def clean_name(name: str) -> str:
    n = name.strip().lower().replace(" ", "_")
    if not NAME_RE.match(n):
        raise ValueError("Use letters, numbers and underscores only (up to 40 characters).")
    return n


class FaceStore:
    def __init__(self, path: Path = DEFAULT_PATH):
        self.path = Path(path)
        self._data: dict = {"people": {}}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data), encoding="utf-8")

    def names(self) -> list[str]:
        return sorted(self._data["people"])

    def add(self, name: str, embeddings: list, can_unlock: bool = False, consent: str = "") -> str:
        name = clean_name(name)
        if not consent:
            raise ValueError("Written consent is needed before saving a face.")
        if not embeddings:
            raise ValueError("No face samples to save.")
        person = self._data["people"].setdefault(name, {"embeddings": []})
        person["embeddings"] += [normalise(e).tolist() for e in embeddings]
        person["can_unlock"] = bool(can_unlock)
        person["consent"] = consent
        person["saved_at"] = datetime.now().isoformat(timespec="seconds")
        self._save()
        return name

    def delete(self, name: str) -> bool:
        name = clean_name(name)
        if name in self._data["people"]:
            del self._data["people"][name]
            self._save()
            return True
        return False

    def people(self) -> dict[str, list]:
        return {n: [np.asarray(e, dtype=np.float32) for e in p["embeddings"]] for n, p in self._data["people"].items()}

    def can_unlock(self, name: str) -> bool:
        return bool(self._data["people"].get(name, {}).get("can_unlock"))
