"""Jarvis: turns a sentence into one allowed action and says what happened.

This is the "brain" for both typing (the app's Jarvis tab) and, later, speech (the voice program in
ai/jarvis only has to turn speech into text and read the reply out loud). Everything goes through
the same Hub methods as the buttons in the app, so the same safety rules apply. Jarvis never
unlocks the door.
"""
import re
from dataclasses import dataclass

from .hub import CommandFailed, CommandRefused, Hub
from .models import ActuatorCommand, DoorCommand

WATER_SECONDS = 10

HELP_TEXT = (
    "I can switch the light, grow light, fan, humidifier and heater, water the plants, lock the door, "
    "arm or disarm the security, and tell you the temperature, humidity, mold risk, plants, door, "
    "who is home and any alerts. I cannot unlock the door."
)

DEVICES = (
    ("growlight", r"\b(grow ?light|plant light|grow lamp)\b"),
    ("humidifier", r"\bhumidifier\b"),
    ("heater", r"\bheater\b"),
    ("fan", r"\bfan\b"),
    ("light", r"\b(lights?|lamp)\b"),
)
NICE = {"light": "Light", "growlight": "Grow light", "fan": "Fan", "humidifier": "Humidifier", "heater": "Heater", "buzzer": "Alarm"}

QUESTION_START = re.compile(r"^(is|are|was|what|what's|whats|how|who|who's|whos|any|anything|does|do|did|has|have|tell me|show me)\b")
POLITE = re.compile(r"^(hey |ok |okay )?(jarvis[ ,]*)?((can|could|would|will) you )?(please )?")


@dataclass
class Intent:
    kind: str
    device: str | None = None
    on: bool | None = None


@dataclass
class Reply:
    ok: bool
    text: str
    intent: str


def normalise(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"[^a-z0-9%?' ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for _ in range(2):  # "hey jarvis, can you please ..."
        t = POLITE.sub("", t).strip()
    t = re.sub(r"\bplease\b", "", t).strip()
    return t


def _device(t: str) -> str | None:
    for name, pattern in DEVICES:
        if re.search(pattern, t):
            return name
    return None


def _verb(t: str) -> bool | None:
    if re.search(r"\b(off|stop|disable|deactivate|kill)\b", t):
        return False
    if re.search(r"\b(on|start|enable|activate)\b", t):
        return True
    return None


def interpret(text: str) -> Intent:
    t = normalise(text)
    if not t:
        return Intent("empty")
    asking = bool(QUESTION_START.match(t))
    device = _device(t)

    if re.search(r"\bhelp\b|what can you do", t):
        return Intent("help")

    if asking:
        if re.search(r"\bmou?ld\b", t):
            return Intent("ask_mold")
        if re.search(r"\b(temperature|humidity|humid|warm|hot|cold|climate|degrees)\b", t):
            return Intent("ask_env")
        if re.search(r"\b(plants?|soil|moisture|thirsty)\b", t):
            return Intent("ask_plants")
        if re.search(r"\bdoor\b|\blocked\b", t):
            return Intent("ask_door")
        if re.search(r"\bwho\b|\banyone\b|\bhome\b", t):
            return Intent("ask_people")
        if re.search(r"\b(alerts?|warnings?|notifications?)\b", t):
            return Intent("ask_alerts")
        if device and _verb(t) is not None:
            return Intent("ask_device", device=device)
        if re.search(r"\b(everything|all)\b.*\b(ok|okay|fine|good|alright)\b|\bstatus\b|\bhouse\b", t):
            return Intent("ask_status")
        return Intent("unknown")

    # commands. Unlocking is recognised only so that it can be refused politely.
    if re.search(r"\b(unlock|open)\b.*\bdoor\b|\bdoor\b.*\b(unlock|open)\b|\blet me in\b", t):
        return Intent("door_unlock")
    if re.search(r"\b(lock|close|secure)\b.*\bdoor\b|\bdoor\b.*\b(lock|close)\b", t):
        return Intent("door_lock")
    if re.search(r"\bdisarm\b", t):
        return Intent("armed", on=False)
    if re.search(r"\barm\b", t):
        return Intent("armed", on=True)
    if re.search(r"\bwater\b", t) and re.search(r"\b(plants?|garden|soil)\b", t):
        return Intent("water")
    if re.search(r"\b(silence|mute|quiet)\b", t) or (re.search(r"\b(alarm|buzzer|siren)\b", t) and _verb(t) is False):
        return Intent("silence")
    if device:
        if re.search(r"\btoggle\b|\bswitch\b(?! (on|off))", t) and _verb(t) is None:
            return Intent("actuator_toggle", device=device)
        verb = _verb(t)
        if verb is None:
            return Intent("clarify", device=device)
        return Intent("actuator", device=device, on=verb)

    if re.search(r"\bmou?ld\b", t):
        return Intent("ask_mold")
    if re.search(r"\b(temperature|humidity|climate)\b", t):
        return Intent("ask_env")
    if re.search(r"\b(plants?|soil)\b", t):
        return Intent("ask_plants")
    if re.search(r"\bwho\b.*\b(home|here)\b|\banyone\b", t):
        return Intent("ask_people")
    if re.search(r"\balerts?\b", t):
        return Intent("ask_alerts")
    if re.search(r"\bstatus\b", t):
        return Intent("ask_status")
    return Intent("unknown")


# ---------------------------------------------------------------- answers
def _env_text(snap: dict) -> str:
    env = snap["env"]
    if "temp_c" not in env:
        return "I do not have a reading from the bathroom yet."
    return f"It is {env['temp_c']:.1f} degrees and {env['humidity']:.0f} percent humidity."


def _mold_text(snap: dict, hub: Hub) -> str:
    env, mold = snap["env"], snap["mold"]
    if "humidity" not in env:
        return "I do not have a reading from the bathroom yet."
    hum, temp = env["humidity"], env["temp_c"]
    if mold["risk"]:
        return f"Yes, there is a mold risk. Humidity is {hum:.0f} percent at {temp:.0f} degrees. Turn on the fan or open a window."
    if hum >= hub.s.mold_humidity_min and hub.s.mold_temp_min <= temp <= hub.s.mold_temp_max:
        return f"Conditions are building: {hum:.0f} percent humidity at {temp:.0f} degrees. Not an alert yet."
    return f"No mold risk right now. Humidity is {hum:.0f} percent."


def _plants_text(snap: dict, hub: Hub) -> str:
    soil = snap["soil"]
    if not soil:
        return "I do not have plant readings yet."
    parts = []
    for p in soil:
        dry = " and dry" if p["moisture_pct"] < hub.s.soil_dry_pct else ""
        parts.append(f"plant {p['id']} is at {p['moisture_pct']:.0f} percent{dry}")
    return ", ".join(parts).capitalize() + "."


def _people_text(snap: dict) -> str:
    home = [p["name"].title() for p in snap["people"] if p["present"]]
    if not home:
        return "I have not recognised anyone at home."
    return f"{_join(home)} {'is' if len(home) == 1 else 'are'} home."


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _alerts_text(hub: Hub) -> str:
    open_alerts = hub.db.alerts(5, only_open=True)
    if not open_alerts:
        return "There are no open alerts."
    first = open_alerts[0]
    more = f" There are {len(open_alerts)} open alerts." if len(open_alerts) > 1 else ""
    return f"Latest: {first['message']}{more}"


def _status_text(snap: dict, hub: Hub) -> str:
    bits = [f"The system is {'armed' if snap['armed'] else 'disarmed'}."]
    locked = snap["door"]["locked"]
    bits.append("The door is locked." if locked else "The door is unlocked." if locked is False else "I do not know the door state.")
    bits.append("There is a mold risk." if snap["mold"]["risk"] else "No mold risk.")
    offline = [n for n, up in snap["nodes"].items() if not up]
    if offline:
        bits.append(f"{_join(offline)} board is offline.")
    n_open = len(hub.db.alerts(50, only_open=True))
    bits.append(f"{n_open} open alert{'s' if n_open != 1 else ''}." if n_open else "No open alerts.")
    return " ".join(bits)


async def run(hub: Hub, text: str) -> Reply:
    intent = interpret(text)
    kind = intent.kind
    snap = hub.snapshot()
    try:
        if kind == "empty":
            return Reply(False, "I did not hear anything.", kind)
        if kind == "help":
            return Reply(True, HELP_TEXT, kind)
        if kind == "unknown":
            return Reply(False, "Sorry, I did not understand that. Say help to hear what I can do.", kind)
        if kind == "clarify":
            return Reply(False, f"Do you want the {NICE[intent.device].lower()} on or off?", kind)
        if kind == "door_unlock":
            return Reply(False, "I cannot unlock the door by voice or text. Use the app, the fingerprint sensor, the keypad or your face.", kind)
        if kind == "door_lock":
            hub.set_door(DoorCommand(action="lock", source="voice"))
            return Reply(True, "Locking the door.", kind)
        if kind == "armed":
            await hub.set_armed(bool(intent.on))
            return Reply(True, "Security armed." if intent.on else "Security disarmed.", kind)
        if kind == "water":
            hub.set_actuator("pump", ActuatorCommand(action="on", seconds=WATER_SECONDS))
            return Reply(True, f"Watering the plants for {WATER_SECONDS} seconds.", kind)
        if kind == "silence":
            hub.set_actuator("buzzer", ActuatorCommand(action="off"))
            return Reply(True, "Alarm silenced.", kind)
        if kind == "actuator":
            hub.set_actuator(intent.device, ActuatorCommand(action="on" if intent.on else "off"))
            return Reply(True, f"{NICE[intent.device]} {'on' if intent.on else 'off'}.", kind)
        if kind == "actuator_toggle":
            now_on = not snap["actuators"].get(intent.device)
            hub.set_actuator(intent.device, ActuatorCommand(action="toggle"))
            return Reply(True, f"{NICE[intent.device]} {'on' if now_on else 'off'}.", kind)
        if kind == "ask_device":
            state = snap["actuators"].get(intent.device)
            if state is None:
                return Reply(True, f"I do not know yet if the {NICE[intent.device].lower()} is on.", kind)
            return Reply(True, f"The {NICE[intent.device].lower()} is {'on' if state else 'off'}.", kind)
        if kind == "ask_env":
            return Reply(True, _env_text(snap), kind)
        if kind == "ask_mold":
            return Reply(True, _mold_text(snap, hub), kind)
        if kind == "ask_plants":
            return Reply(True, _plants_text(snap, hub), kind)
        if kind == "ask_door":
            locked = snap["door"]["locked"]
            return Reply(True, "The door is locked." if locked else "The door is unlocked." if locked is False else "I do not know the door state yet.", kind)
        if kind == "ask_people":
            return Reply(True, _people_text(snap), kind)
        if kind == "ask_alerts":
            return Reply(True, _alerts_text(hub), kind)
        if kind == "ask_status":
            return Reply(True, _status_text(snap, hub), kind)
    except CommandRefused as e:
        return Reply(False, str(e), kind)
    except CommandFailed:
        return Reply(False, "I could not reach the house. Is the message broker running?", kind)
    return Reply(False, "Sorry, I did not understand that.", "unknown")
