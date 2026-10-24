"""A tiny MQTT broker for development, so nothing needs installing.

Run:  python tools/dev_broker.py
For the real boards on your Wi-Fi use Mosquitto instead (see docker-compose.yml in the repo root).
"""
import asyncio
import logging

from amqtt.broker import Broker

CONFIG = {
    "listeners": {"default": {"type": "tcp", "bind": "127.0.0.1:1883"}},
    "sys_interval": 0,
    "auth": {"allow-anonymous": True, "plugins": ["auth_anonymous"]},
    "topic-check": {"enabled": False},
}


async def main():
    broker = Broker(CONFIG)
    await broker.start()
    print("Dev broker running on 127.0.0.1:1883 (Ctrl+C to stop)")
    await asyncio.Event().wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
