import json
import logging
from collections.abc import Callable

import paho.mqtt.client as mqtt

from .config import Settings

log = logging.getLogger("home.mqtt")

SUBSCRIPTIONS = [
    "home/env/+",
    "home/plant/soil",
    "home/sensor/fire",
    "home/door/state",
    "home/door/access",
    "home/actuator/+/state",
    "home/camera/event",
    "home/node/+/status",
]


class MqttBridge:
    """Connects to the MQTT broker and reconnects by itself if it drops."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.connected = False
        self.on_message: Callable[[str, bytes], None] = lambda topic, payload: None
        self.on_connected: Callable[[], None] = lambda: None
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="home-server")
        if settings.mqtt_username:
            self._client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def start(self) -> None:
        log.info("Connecting to MQTT broker at %s:%s", self.settings.mqtt_host, self.settings.mqtt_port)
        self._client.connect_async(self.settings.mqtt_host, self.settings.mqtt_port, keepalive=30)
        self._client.loop_start()

    def stop(self) -> None:
        self._client.loop_stop()
        try:
            self._client.disconnect()
        except Exception:  # shutting down anyway
            pass

    def publish(self, topic: str, payload: dict, retain: bool = False) -> bool:
        if not self.connected:
            log.warning("Not connected to the broker, dropped message for %s", topic)
            return False
        info = self._client.publish(topic, json.dumps(payload), qos=1, retain=retain)
        return info.rc == mqtt.MQTT_ERR_SUCCESS

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            log.error("Broker refused the connection: %s", reason_code)
            return
        self.connected = True
        log.info("Connected to the broker")
        for topic in SUBSCRIPTIONS:
            client.subscribe(topic, qos=1)
        try:
            self.on_connected()
        except Exception:
            log.exception("on_connected hook failed")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        self.connected = False
        log.warning("Disconnected from the broker (%s), will retry", reason_code)

    def _on_message(self, client, userdata, msg):
        try:
            self.on_message(msg.topic, bytes(msg.payload))
        except Exception:
            log.exception("Error handling message on %s", msg.topic)
