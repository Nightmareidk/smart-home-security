from dataclasses import dataclass, field

from .config import Settings
from .state import HomeState


@dataclass
class Alert:
    type: str
    severity: str  # info, warning, critical
    message: str
    data: dict = field(default_factory=dict)
    speak: bool = False  # should Jarvis say it out loud


class RuleEngine:
    """Decides when something is worth an alert. Pure logic: no network, no database.

    The caller updates the state first, then asks the engine what to do about it.
    Time is passed in, so tests can control it.
    """

    def __init__(self, settings: Settings, state: HomeState):
        self.s = settings
        self.state = state
        self._last_alert: dict[str, float] = {}
        self._failed_attempts: list[float] = []

    def _cooldown_ok(self, key: str, now: float, cooldown: float | None = None) -> bool:
        wait = self.s.alert_cooldown if cooldown is None else cooldown
        last = self._last_alert.get(key)
        if last is not None and now - last < wait:
            return False
        self._last_alert[key] = now
        return True

    # ---- sensors -----------------------------------------------------------

    def on_env(self, now: float) -> list[Alert]:
        env = self.state.env
        damp_and_warm = (
            env["humidity"] >= self.s.mold_humidity_min
            and self.s.mold_temp_min <= env["temp_c"] <= self.s.mold_temp_max
        )
        alerts: list[Alert] = []
        if damp_and_warm:
            if self.state.mold_since is None:
                self.state.mold_since = now
        else:
            if self.state.mold_risk:
                alerts.append(Alert("mold_risk", "info", "Humidity and temperature are back to safe levels."))
            self.state.mold_since = None
            self.state.mold_risk = False
        return alerts + self.tick(now)

    def tick(self, now: float) -> list[Alert]:
        """Called every second so time-based rules still fire when no new reading arrives."""
        st = self.state
        if st.mold_since is not None and not st.mold_risk and now - st.mold_since >= self.s.mold_hold_seconds:
            st.mold_risk = True
            env = st.env
            minutes = max(1, round((now - st.mold_since) / 60))
            return [
                Alert(
                    "mold_risk",
                    "warning",
                    f"Mold risk: humidity {env['humidity']:.0f}% and {env['temp_c']:.0f} °C "
                    f"for about {minutes} min. Switch on the fan or open a window.",
                    {"humidity": env["humidity"], "temp_c": env["temp_c"]},
                    speak=True,
                )
            ]
        return []

    def on_soil(self, now: float) -> list[Alert]:
        alerts = []
        for pid, moisture in self.state.soil.items():
            if moisture < self.s.soil_dry_pct and self._cooldown_ok(f"plant_dry:{pid}", now, 300):
                alerts.append(
                    Alert("plant_dry", "warning", f"Plant {pid} is dry ({moisture:.0f}%).", {"plant": pid, "moisture_pct": moisture})
                )
        return alerts

    def on_fire_sensor(self, now: float) -> list[Alert]:
        fire = self.state.fire
        if (fire.get("flame") or fire.get("gas_level", 0) >= self.s.gas_alert_level) and self._cooldown_ok("fire", now, 30):
            why = "flame sensor" if fire.get("flame") else "gas sensor"
            return [Alert("fire", "critical", f"Possible fire: {why} triggered.", dict(fire), speak=True)]
        return []

    # ---- camera and door ---------------------------------------------------

    def on_camera(self, event: dict, now: float) -> list[Alert]:
        kind = event.get("type")
        confidence = event.get("confidence")
        confident = isinstance(confidence, (int, float)) and confidence >= self.s.camera_min_confidence
        name = event.get("name") if isinstance(event.get("name"), str) and event.get("name") else None
        snapshot = event.get("snapshot") if isinstance(event.get("snapshot"), str) else None
        data = {"type": kind, "confidence": confidence, "name": name, "snapshot": snapshot}

        if name:
            self.state.mark_present(name, now)
        if kind in ("fire", "smoke"):
            if confident and self._cooldown_ok("fire", now, 30):
                return [Alert("fire", "critical", f"Camera sees {kind}.", data, speak=True)]
            return []
        if kind == "person" and not name and confident:
            if self.state.armed and self._cooldown_ok("intrusion", now, 20):
                return [Alert("intrusion", "critical", "Possible intruder: unknown person while the system is armed.", data, speak=True)]
            if self._cooldown_ok("unknown_person", now, 60):
                return [Alert("unknown_person", "info", "An unknown person was seen by the camera.", data)]
        return []

    def on_access(self, event: dict, now: float) -> list[Alert]:
        success = event.get("success")
        user = event.get("user") if isinstance(event.get("user"), str) and event.get("user") else None
        method = event.get("method", "unknown")
        if success is True:
            if user:
                self.state.mark_present(user, now)
            self._failed_attempts.clear()
            return []
        if success is False:
            self._failed_attempts = [t for t in self._failed_attempts if now - t <= self.s.failed_unlock_window]
            self._failed_attempts.append(now)
            if len(self._failed_attempts) >= self.s.failed_unlock_limit and self._cooldown_ok("door_failed", now, 60):
                return [
                    Alert(
                        "door_failed_attempts",
                        "critical" if self.state.armed else "warning",
                        f"{len(self._failed_attempts)} failed door attempts in a minute (last: {method}).",
                        {"method": method},
                        speak=True,
                    )
                ]
        return []

    def on_node(self, name: str, online: bool, now: float) -> list[Alert]:
        if not online and self._cooldown_ok(f"node_offline:{name}", now, 30):
            return [Alert("node_offline", "warning", f"The {name} board went offline.", {"node": name})]
        return []
