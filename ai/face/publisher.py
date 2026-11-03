import json
import logging
import time

import paho.mqtt.client as mqtt

log = logging.getLogger("vision.mqtt")
TOPIC = "home/camera/event"


class EventPublisher:
    """Sends camera events to the message broker. Reconnects by itself."""

    def __init__(self, host: str, port: int):
        self.connected = False
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="face-ai")
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.connect_async(host, port, keepalive=30)
        self._client.loop_start()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        self.connected = reason_code == 0
        log.info("Connected to the broker" if self.connected else "Broker refused the connection")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        self.connected = False
        log.warning("Lost the broker, will retry")

    def wait_until_connected(self, timeout: float = 3.0) -> bool:
        """Give the broker a moment to answer, so the very first event is not lost."""
        end = time.time() + timeout
        while not self.connected and time.time() < end:
            time.sleep(0.05)
        return self.connected

    def publish(self, event: dict) -> bool:
        if not self.connected:
            log.warning("Not connected to the broker, dropped %s", event.get("type"))
            return False
        info = self._client.publish(TOPIC, json.dumps(event), qos=1)
        return info.rc == mqtt.MQTT_ERR_SUCCESS

    def close(self) -> None:
        self._client.loop_stop()
        try:
            self._client.disconnect()
        except Exception:
            pass
