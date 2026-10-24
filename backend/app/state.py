from dataclasses import dataclass, field
from typing import Any

from .models import ACTUATORS


def _num(value: Any, low: float, high: float) -> float | None:
    """Return the value as a number if it is a real number inside the range, else None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value != value or not (low <= value <= high):  # NaN or out of range
        return None
    return float(value)


@dataclass
class HomeState:
    """What the house looks like right now. Only the newest values are kept here."""

    env: dict = field(default_factory=dict)
    soil: dict[int, float] = field(default_factory=dict)
    fire: dict = field(default_factory=dict)
    door_locked: bool | None = None
    actuators: dict[str, bool | None] = field(default_factory=lambda: {n: None for n in ACTUATORS})
    armed: bool = False
    nodes: dict[str, bool] = field(default_factory=dict)
    people: dict[str, float] = field(default_factory=dict)  # name -> last seen time
    last_camera: dict | None = None
    mold_since: float | None = None
    mold_risk: bool = False
    updated_at: float = 0.0

    # Each apply_* returns True when the data was accepted, so bad messages can be ignored.

    def apply_env(self, data: dict, now: float) -> bool:
        temp = _num(data.get("temp_c"), -40, 85)
        hum = _num(data.get("humidity"), 0, 100)
        if temp is None or hum is None:
            return False
        env = {"temp_c": temp, "humidity": hum, "ts": now}
        iaq = _num(data.get("iaq"), 0, 100)
        if iaq is not None:
            env["iaq"] = iaq
        pressure = _num(data.get("pressure_hpa"), 300, 1100)
        if pressure is not None:
            env["pressure_hpa"] = pressure
        self.env = env
        self.updated_at = now
        return True

    def apply_soil(self, data: dict, now: float) -> bool:
        plants = data.get("plants")
        if not isinstance(plants, list):
            return False
        accepted = False
        for p in plants[:16]:
            if not isinstance(p, dict):
                continue
            pid = p.get("id")
            moisture = _num(p.get("moisture_pct"), 0, 100)
            if isinstance(pid, int) and not isinstance(pid, bool) and 0 <= pid < 100 and moisture is not None:
                self.soil[pid] = moisture
                accepted = True
        if accepted:
            self.updated_at = now
        return accepted

    def apply_fire(self, data: dict, now: float) -> bool:
        flame = data.get("flame")
        gas = _num(data.get("gas_level"), 0, 100)
        if not isinstance(flame, bool) and gas is None:
            return False
        self.fire = {"flame": flame if isinstance(flame, bool) else False, "gas_level": gas or 0.0, "ts": now}
        self.updated_at = now
        return True

    def apply_door_state(self, data: dict, now: float) -> bool:
        locked = data.get("locked")
        if not isinstance(locked, bool):
            return False
        self.door_locked = locked
        self.updated_at = now
        return True

    def apply_actuator(self, name: str, data: dict, now: float) -> bool:
        on = data.get("on")
        if name not in self.actuators or not isinstance(on, bool):
            return False
        self.actuators[name] = on
        self.updated_at = now
        return True

    def apply_node(self, name: str, data: dict, now: float) -> bool:
        online = data.get("online")
        if not isinstance(online, bool) or not (1 <= len(name) <= 24):
            return False
        self.nodes[name] = online
        self.updated_at = now
        return True

    def mark_present(self, name: str, now: float) -> None:
        self.people[name] = now
        self.updated_at = now

    def present_people(self, now: float, timeout: float) -> list[dict]:
        return [
            {"name": n, "last_seen": t, "present": now - t <= timeout}
            for n, t in sorted(self.people.items())
        ]

    def snapshot(self, now: float, present_timeout: float) -> dict:
        return {
            "env": self.env,
            "soil": [{"id": i, "moisture_pct": m} for i, m in sorted(self.soil.items())],
            "fire": self.fire,
            "door": {"locked": self.door_locked},
            "actuators": self.actuators,
            "armed": self.armed,
            "nodes": self.nodes,
            "people": self.present_people(now, present_timeout),
            "mold": {
                "risk": self.mold_risk,
                "building_seconds": round(now - self.mold_since, 1) if self.mold_since else 0,
            },
            "last_camera": self.last_camera,
            "ts": now,
        }
