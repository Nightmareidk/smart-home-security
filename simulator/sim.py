"""Simulator: pretends to be the door, plant and camera boards.

It follows docs/CONTRACT.md exactly, so the server and the app can be built and tested without
any hardware. When the real boards are ready they replace this program.

Run it (needs a broker running, see the repo README):
    python sim.py                      start the pretend house
    python sim.py scenario mold        in another terminal: make the bathroom damp and warm
    python sim.py scenario list        show all scenarios
"""
import argparse
import json
import random
import threading
import time

import paho.mqtt.client as mqtt

ACTUATORS = ("light", "growlight", "pump", "fan", "humidifier", "heater", "buzzer")
SCENARIOS = {
    "normal": "Everything back to calm",
    "mold": "Humidifier on: the air gets damp and warm until a mold-risk alert fires",
    "fire": "Flame and gas sensors trip, and the camera sees fire",
    "intruder": "The camera sees an unknown person",
    "known": "Sara arrives: fingerprint unlock, camera recognises her, door relocks",
    "dry": "Plant 1 dries out",
    "failed": "Three wrong keypad attempts at the door",
    "offline": "The plant board drops off the network for 15 seconds",
}


class World:
    """The pretend house. All the numbers live here."""

    def __init__(self):
        self.lock = threading.Lock()
        self.temp = 24.0
        self.humidity = 52.0
        self.iaq = 85.0
        self.soil = {1: 55.0, 2: 48.0}
        self.flame = False
        self.gas = 8.0
        self.locked = True
        self.actuators = {name: False for name in ACTUATORS}
        self.off_at: dict[str, float] = {}
        self.plant_online = True

    def step(self, dt: float, now: float) -> list[str]:
        """Move the numbers forward. Returns the names of switches that turned themselves off."""
        with self.lock:
            hum_target = 52.0
            if self.actuators["humidifier"]:
                hum_target = 92.0
            if self.actuators["fan"]:
                hum_target = (hum_target + 40.0) / 2 if self.actuators["humidifier"] else 42.0
            temp_target = 28.0 if self.actuators["heater"] else 24.0
            if self.actuators["humidifier"]:
                temp_target = max(temp_target, 26.0)
            self.humidity += (hum_target - self.humidity) * min(1.0, 0.06 * dt) + random.uniform(-0.15, 0.15)
            self.temp += (temp_target - self.temp) * min(1.0, 0.03 * dt) + random.uniform(-0.03, 0.03)
            self.humidity = max(0.0, min(100.0, self.humidity))
            self.iaq = max(0.0, min(100.0, self.iaq + (85 - self.iaq) * 0.02 * dt - (0.05 if self.humidity > 75 else 0)))
            for pid in self.soil:
                gain = 1.2 * dt if self.actuators["pump"] else 0.0
                self.soil[pid] = max(0.0, min(100.0, self.soil[pid] - 0.03 * dt + gain))
            if not self.flame:
                self.gas += (8.0 - self.gas) * min(1.0, 0.1 * dt)
            expired = [n for n, t in self.off_at.items() if now >= t]
            for n in expired:
                self.actuators[n] = False
                del self.off_at[n]
            return expired


class Node:
    """One pretend board with its own MQTT connection and 'last will'."""

    def __init__(self, name: str, host: str, port: int, subscriptions: list[str]):
        self.name = name
        self.subscriptions = subscriptions
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"sim-{name}")
        self.client.will_set(f"home/node/{name}/status", json.dumps({"online": False}), qos=1, retain=True)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.handlers: list = []
        self.client.connect(host, port, keepalive=30)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        for topic in self.subscriptions:
            client.subscribe(topic, qos=1)
        self.send(f"home/node/{self.name}/status", {"online": True}, retain=True)

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload)
        except ValueError:
            return
        if isinstance(data, dict):
            for handler in self.handlers:
                handler(msg.topic, data)

    def send(self, topic: str, payload: dict, retain: bool = False) -> None:
        self.client.publish(topic, json.dumps(payload), qos=1, retain=retain)

    def stop(self) -> None:
        self.send(f"home/node/{self.name}/status", {"online": False}, retain=True)
        time.sleep(0.2)
        self.client.loop_stop()
        self.client.disconnect()


class House:
    def __init__(self, host: str, port: int, speed: float):
        self.world = World()
        self.speed = speed
        self.door = Node("door", host, port, ["home/door/command"])
        self.plant = Node("plant", host, port, ["home/actuator/+/command"])
        self.cam = Node("cam", host, port, ["home/sim/scenario"])
        self.door.handlers.append(self.on_door_command)
        self.plant.handlers.append(self.on_actuator_command)
        self.cam.handlers.append(self.on_scenario)
        # announce starting state (the real boards do this too)
        time.sleep(0.5)
        self.send_door_state()
        for name in ACTUATORS:
            self.send_actuator_state(name)

    # ---- what the boards report -------------------------------------------

    def send_door_state(self):
        self.door.send("home/door/state", {"locked": self.world.locked}, retain=True)

    def send_actuator_state(self, name: str):
        self.plant.send(f"home/actuator/{name}/state", {"on": self.world.actuators[name]}, retain=True)

    def publish_sensors(self):
        w = self.world
        if not w.plant_online:
            return
        with w.lock:
            env = {"temp_c": round(w.temp, 1), "humidity": round(w.humidity, 1), "iaq": round(w.iaq), "pressure_hpa": 1011}
            soil = {"plants": [{"id": pid, "moisture_pct": round(v)} for pid, v in w.soil.items()]}
            fire = {"flame": w.flame, "gas_level": round(w.gas)}
        self.plant.send("home/env/bathroom", env)
        self.plant.send("home/plant/soil", soil)
        self.plant.send("home/sensor/fire", fire)

    # ---- what the boards obey ---------------------------------------------

    def on_actuator_command(self, topic: str, data: dict):
        parts = topic.split("/")
        name = parts[2] if len(parts) == 4 else ""
        if name not in ACTUATORS or data.get("action") not in ("on", "off"):
            return
        on = data["action"] == "on"
        with self.world.lock:
            self.world.actuators[name] = on
            if on and isinstance(data.get("seconds"), (int, float)):
                self.world.off_at[name] = time.time() + float(data["seconds"]) / self.speed
            else:
                self.world.off_at.pop(name, None)
        print(f"  {name} -> {'ON' if on else 'off'}")
        self.send_actuator_state(name)

    def on_door_command(self, topic: str, data: dict):
        if data.get("action") not in ("lock", "unlock"):
            return
        self.world.locked = data["action"] == "lock"
        print(f"  door -> {'locked' if self.world.locked else 'UNLOCKED'}")
        self.send_door_state()

    # ---- scenarios ---------------------------------------------------------

    def on_scenario(self, topic: str, data: dict):
        name = data.get("name")
        if name not in SCENARIOS:
            return
        print(f"Scenario: {name}")
        threading.Thread(target=self.run_scenario, args=(name,), daemon=True).start()

    def set_actuator(self, name: str, on: bool):
        with self.world.lock:
            self.world.actuators[name] = on
        self.send_actuator_state(name)

    def run_scenario(self, name: str):
        w = self.world
        if name == "normal":
            with w.lock:
                w.humidity, w.temp, w.flame, w.gas = 52.0, 24.0, False, 8.0
                w.soil = {1: 55.0, 2: 48.0}
            for a in ("humidifier", "heater", "fan", "pump", "buzzer"):
                self.set_actuator(a, False)
        elif name == "mold":
            with w.lock:
                w.humidity, w.temp = 68.0, 25.0
            self.set_actuator("humidifier", True)
        elif name == "fire":
            with w.lock:
                w.flame, w.gas = True, 85.0
            self.cam.send("home/camera/event", {"type": "fire", "confidence": 0.9})
        elif name == "intruder":
            for _ in range(2):
                self.cam.send("home/camera/event", {"type": "person", "confidence": 0.93})
                time.sleep(1)
        elif name == "known":
            self.cam.send("home/camera/event", {"type": "person", "confidence": 0.95, "name": "sara"})
            self.door.send("home/door/access", {"method": "fingerprint", "user": "sara", "success": True})
            self.world.locked = False
            self.send_door_state()
            time.sleep(5)
            self.world.locked = True
            self.send_door_state()
        elif name == "dry":
            with w.lock:
                w.soil[1] = 12.0
        elif name == "failed":
            for _ in range(3):
                self.door.send("home/door/access", {"method": "keypad", "success": False})
                time.sleep(0.5)
        elif name == "offline":
            w.plant_online = False
            self.plant.send("home/node/plant/status", {"online": False}, retain=True)
            time.sleep(15)
            w.plant_online = True
            self.plant.send("home/node/plant/status", {"online": True}, retain=True)

    # ---- main loop ---------------------------------------------------------

    def run(self, interval: float):
        print(f"Pretend house running. Sensors every {interval}s, speed x{self.speed:g}. Ctrl+C to stop.")
        last = time.time()
        while True:
            time.sleep(interval)
            now = time.time()
            expired = self.world.step((now - last) * self.speed, now)
            last = now
            for name in expired:
                print(f"  {name} -> off (timer)")
                self.send_actuator_state(name)
            self.publish_sensors()

    def stop(self):
        for node in (self.door, self.plant, self.cam):
            node.stop()


def send_scenario(host: str, port: int, name: str):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="sim-control")
    client.connect(host, port)
    client.loop_start()
    info = client.publish("home/sim/scenario", json.dumps({"name": name}), qos=1)
    info.wait_for_publish(5)
    client.loop_stop()
    client.disconnect()
    print(f"Sent scenario: {name}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", nargs="?", choices=["run", "scenario"], default="run")
    p.add_argument("name", nargs="?", help="scenario name, or 'list'")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--interval", type=float, default=2.0, help="seconds between sensor messages")
    p.add_argument("--speed", type=float, default=1.0, help="make the house change faster, for demos")
    args = p.parse_args()

    if args.command == "scenario":
        if not args.name or args.name == "list":
            for key, text in SCENARIOS.items():
                print(f"  {key:9} {text}")
            return
        if args.name not in SCENARIOS:
            p.error(f"unknown scenario '{args.name}'. Try: python sim.py scenario list")
        send_scenario(args.host, args.port, args.name)
        return

    house = House(args.host, args.port, args.speed)
    try:
        house.run(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        house.stop()


if __name__ == "__main__":
    main()
