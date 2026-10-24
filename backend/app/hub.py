import asyncio
import json
import logging
import time
from collections.abc import Callable
from typing import Any

from .config import Settings
from .db import Database, valid_metric
from .models import ACTUATORS, ActuatorCommand, DoorCommand, LabResult
from .rules import Alert, RuleEngine
from .state import HomeState

log = logging.getLogger("home.hub")

MAX_PAYLOAD_BYTES = 4096
ACCESS_METHODS = {"fingerprint", "keypad", "face", "app"}
CAMERA_TYPES = {"person", "movement", "fire", "smoke", "face"}
PUMP_MAX_SECONDS = 60.0
PUMP_DEFAULT_SECONDS = 10.0

Publish = Callable[..., bool]


class CommandRefused(Exception):
    """The command is not allowed (for example, unlocking the door by voice)."""


class CommandFailed(Exception):
    """The command was allowed but could not be sent (broker is down)."""


class Hub:
    """The middle of the server: takes in messages, keeps the state, raises alerts, runs commands."""

    def __init__(self, settings: Settings, db: Database, publish: Publish, clock: Callable[[], float] = time.time):
        self.s = settings
        self.db = db
        self.publish = publish
        self.now = clock
        self.state = HomeState()
        self.rules = RuleEngine(settings, self.state)
        self.clients: set[Any] = set()  # websockets: anything with an async send_json
        self._last_stored: dict[str, float] = {}
        self.state.armed = db.get_setting("armed", "0") == "1"

    # ---- live clients ------------------------------------------------------

    async def broadcast(self, message: dict) -> None:
        dead = []
        for client in list(self.clients):
            try:
                await client.send_json(message)
            except Exception:
                dead.append(client)
        for client in dead:
            self.clients.discard(client)

    def snapshot(self) -> dict:
        return self.state.snapshot(self.now(), self.s.present_timeout)

    # ---- incoming messages -------------------------------------------------

    async def handle_message(self, topic: str, raw: bytes) -> None:
        if len(raw) > MAX_PAYLOAD_BYTES:
            log.warning("Ignored oversized message on %s", topic)
            return
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            log.warning("Ignored message that is not JSON on %s", topic)
            return
        if not isinstance(data, dict):
            return

        now = self.now()
        alerts: list[Alert] = []
        parts = topic.split("/")
        accepted = False

        if parts[:1] != ["home"]:
            return
        match parts[1:]:
            case ["env", "bathroom"]:
                accepted = self.state.apply_env(data, now)
                if accepted:
                    env = self.state.env
                    self._store("temp_c", env["temp_c"], now)
                    self._store("humidity", env["humidity"], now)
                    if "iaq" in env:
                        self._store("iaq", env["iaq"], now)
                    alerts = self.rules.on_env(now)
            case ["plant", "soil"]:
                accepted = self.state.apply_soil(data, now)
                if accepted:
                    for pid, moisture in self.state.soil.items():
                        self._store(f"soil_{pid}", moisture, now)
                    alerts = self.rules.on_soil(now)
            case ["sensor", "fire"]:
                accepted = self.state.apply_fire(data, now)
                if accepted:
                    alerts = self.rules.on_fire_sensor(now)
            case ["door", "state"]:
                accepted = self.state.apply_door_state(data, now)
            case ["door", "access"]:
                accepted = self._handle_access(data, now)
                if accepted:
                    alerts = self.rules.on_access(data, now)
            case ["actuator", name, "state"] if name in ACTUATORS:
                accepted = self.state.apply_actuator(name, data, now)
            case ["camera", "event"]:
                accepted = data.get("type") in CAMERA_TYPES
                if accepted:
                    alerts = self.rules.on_camera(data, now)
                    self.state.last_camera = {
                        "type": data.get("type"),
                        "confidence": data.get("confidence"),
                        "name": data.get("name") if isinstance(data.get("name"), str) else None,
                        "snapshot": data.get("snapshot") if isinstance(data.get("snapshot"), str) else None,
                        "ts": now,
                    }
            case ["node", name, "status"]:
                accepted = self.state.apply_node(name, data, now)
                if accepted:
                    alerts = self.rules.on_node(name, self.state.nodes[name], now)
            case _:
                return

        if not accepted:
            log.warning("Ignored invalid message on %s", topic)
            return
        await self._publish_alerts(alerts)
        await self.broadcast({"type": "state", "data": self.snapshot()})

    def _handle_access(self, data: dict, now: float) -> bool:
        method, success = data.get("method"), data.get("success")
        user = data.get("user")
        if method not in ACCESS_METHODS or not isinstance(success, bool):
            return False
        if user is not None and (not isinstance(user, str) or len(user) > 40):
            return False
        self.db.add_access(now, method, user or None, success)
        return True

    def _store(self, metric: str, value: float, now: float) -> None:
        """Save a reading, but only every few seconds so the database does not fill up."""
        last = self._last_stored.get(metric)
        if last is None or now - last >= self.s.reading_store_interval:
            self._last_stored[metric] = now
            self.db.add_reading(metric, value, now)

    # ---- alerts ------------------------------------------------------------

    async def _publish_alerts(self, alerts: list[Alert]) -> None:
        for a in alerts:
            ts = self.now()
            alert_id = self.db.add_alert(ts, a.type, a.severity, a.message, a.data)
            payload = {"id": alert_id, "type": a.type, "severity": a.severity, "message": a.message, "ts": ts}
            self.publish("home/alert", payload)
            if a.speak:
                self.publish("home/jarvis/say", {"text": a.message})
            await self.broadcast({"type": "alert", "data": {**payload, "data": a.data, "acknowledged": False}})

    async def tick(self) -> None:
        alerts = self.rules.tick(self.now())
        if alerts:
            await self._publish_alerts(alerts)
            await self.broadcast({"type": "state", "data": self.snapshot()})

    async def run_ticker(self) -> None:
        while True:
            await asyncio.sleep(1)
            try:
                await self.tick()
            except Exception:
                log.exception("tick failed")

    # ---- commands (from the app or Jarvis) --------------------------------

    def set_actuator(self, name: str, cmd: ActuatorCommand) -> dict:
        if name not in ACTUATORS:
            raise CommandRefused("Unknown device")
        action = cmd.action
        if action == "toggle":
            action = "off" if self.state.actuators.get(name) else "on"
        payload: dict = {"action": action}
        seconds = cmd.seconds
        if name == "pump" and action == "on":
            # The pump must never be left running, so it always gets a time limit.
            seconds = min(seconds or PUMP_DEFAULT_SECONDS, PUMP_MAX_SECONDS)
        if seconds is not None and action == "on":
            payload["seconds"] = seconds
        if not self.publish(f"home/actuator/{name}/command", payload):
            raise CommandFailed("Could not reach the house. Is the broker running?")
        return payload

    def set_door(self, cmd: DoorCommand) -> dict:
        if cmd.action == "unlock" and cmd.source == "voice":
            raise CommandRefused("The door cannot be unlocked by voice. Use the app, fingerprint, keypad or face.")
        if not self.publish("home/door/command", {"action": cmd.action}):
            raise CommandFailed("Could not reach the house. Is the broker running?")
        if cmd.action == "unlock":
            self.db.add_access(self.now(), "app", None, True)
        return {"action": cmd.action}

    async def set_armed(self, armed: bool) -> None:
        self.state.armed = armed
        self.db.set_setting("armed", "1" if armed else "0")
        self.publish_armed()
        await self.broadcast({"type": "state", "data": self.snapshot()})

    def publish_armed(self) -> None:
        self.publish("home/security/armed", {"armed": self.state.armed}, retain=True)

    def add_lab_result(self, result: LabResult) -> int:
        return self.db.add_lab_result(self.now(), result.result, result.target, result.notes, result.author)

    # ---- history -----------------------------------------------------------

    def readings(self, metric: str, limit: int, since_seconds: float) -> list[dict] | None:
        if not valid_metric(metric):
            return None
        since = self.now() - since_seconds if since_seconds > 0 else 0.0
        return self.db.readings(metric, limit, since)
