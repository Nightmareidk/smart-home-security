"""Jarvis speaks important alerts out loud when the house server publishes them on home/jarvis/say."""
import json
import logging
import queue
import threading
import time

log = logging.getLogger("jarvis.alerts")
TOPIC = "home/jarvis/say"
MAX_TEXT = 200


class Deduper:
    """Stops the same sentence being spoken again and again."""

    def __init__(self, seconds: float = 20.0):
        self.seconds = seconds
        self._last: dict[str, float] = {}

    def allow(self, text: str, now: float) -> bool:
        last = self._last.get(text)
        if last is not None and now - last < self.seconds:
            return False
        self._last[text] = now
        return True


def clean(payload: bytes) -> str | None:
    """The sentence to speak, or None if the message is not a proper one."""
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        return None
    text = data.get("text") if isinstance(data, dict) else None
    if not isinstance(text, str) or not text.strip():
        return None
    return text.strip()[:MAX_TEXT]


class AlertListener:
    def __init__(self, host: str, port: int, speak):
        import paho.mqtt.client as mqtt

        self.speak = speak
        self.deduper = Deduper()
        self.queue: queue.Queue[str] = queue.Queue(maxsize=10)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="jarvis-voice")
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.client.on_connect = lambda c, u, f, rc, p=None: c.subscribe(TOPIC, qos=1)
        self.client.on_message = self._on_message
        self.client.connect_async(host, port, keepalive=30)
        self.client.loop_start()
        threading.Thread(target=self._worker, daemon=True).start()

    def _on_message(self, client, userdata, msg):
        text = clean(bytes(msg.payload))
        if text and not self.queue.full():
            self.queue.put(text)

    def _worker(self):
        while True:
            text = self.queue.get()
            if not self.deduper.allow(text, time.time()):
                continue
            try:
                log.info("Alert: %s", text)
                self.speak(text)
            except Exception:
                log.exception("Could not speak the alert")

    def close(self):
        self.client.loop_stop()
