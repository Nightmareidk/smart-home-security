import os

os.environ["HOME_MQTT_ENABLED"] = "false"
os.environ["HOME_DB_PATH"] = ":memory:"
os.environ["HOME_API_TOKEN"] = "test-token"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.jarvis import interpret  # noqa: E402
from app.main import app  # noqa: E402

AUTH = {"Authorization": "Bearer test-token"}


@pytest.mark.parametrize(
    "text,kind,device,on",
    [
        ("turn on the light", "actuator", "light", True),
        ("Hey Jarvis, turn the light off", "actuator", "light", False),
        ("Jarvis, can you please switch on the fan?", "actuator", "fan", True),
        ("lights on", "actuator", "light", True),
        ("turn on the grow light", "actuator", "growlight", True),
        ("stop the humidifier", "actuator", "humidifier", False),
        ("switch the fan", "actuator_toggle", "fan", None),
        ("turn the fan", "clarify", "fan", None),
        ("water the plants", "water", None, None),
        ("lock the door", "door_lock", None, None),
        ("unlock the door", "door_unlock", None, None),
        ("open the door", "door_unlock", None, None),
        ("let me in", "door_unlock", None, None),
        ("arm the system", "armed", None, True),
        ("disarm security", "armed", None, False),
        ("silence the alarm", "silence", None, None),
        ("turn off the alarm", "silence", None, None),
        ("what is the temperature", "ask_env", None, None),
        ("what's the humidity?", "ask_env", None, None),
        ("is there a mold risk", "ask_mold", None, None),
        ("how are the plants", "ask_plants", None, None),
        ("is the door locked", "ask_door", None, None),
        ("who is home", "ask_people", None, None),
        ("is anyone here", "ask_people", None, None),
        ("any alerts today", "ask_alerts", None, None),
        ("is everything ok", "ask_status", None, None),
        ("is the light on", "ask_device", "light", None),
        ("help", "help", None, None),
        ("sing me a song", "unknown", None, None),
    ],
)
def test_sentences_become_the_right_action(text, kind, device, on):
    intent = interpret(text)
    assert intent.kind == kind
    assert intent.device == device
    assert intent.on == on


@pytest.fixture()
def client():
    with TestClient(app) as c:
        hub = app.state.hub
        published = []
        hub.publish = lambda topic, payload, retain=False: published.append((topic, payload)) or True
        c.published = published
        c.hub = hub
        yield c


def ask(client, text):
    r = client.post("/api/jarvis", headers=AUTH, json={"text": text})
    assert r.status_code == 200
    return r.json()


def test_jarvis_switches_things_through_the_same_rules(client):
    assert ask(client, "turn on the fan")["reply"] == "Fan on."
    assert ("home/actuator/fan/command", {"action": "on"}) in client.published
    ask(client, "water the plants")
    assert ("home/actuator/pump/command", {"action": "on", "seconds": 10}) in client.published


def test_jarvis_never_unlocks_the_door(client):
    for phrase in ("unlock the door", "Hey Jarvis, open the door please", "let me in"):
        r = ask(client, phrase)
        assert r["ok"] is False and "cannot unlock" in r["reply"]
    assert not any(t == "home/door/command" for t, _ in client.published)
    assert ask(client, "lock the door")["ok"] is True
    assert ("home/door/command", {"action": "lock"}) in client.published


def test_jarvis_answers_from_the_live_state(client):
    assert "do not have a reading" in ask(client, "what is the temperature")["reply"]
    import json
    client.portal.call(client.hub.handle_message, "home/env/bathroom", json.dumps({"temp_c": 24.3, "humidity": 58}).encode())
    assert ask(client, "what is the temperature")["reply"] == "It is 24.3 degrees and 58 percent humidity."
    assert "No mold risk" in ask(client, "is there a mold risk")["reply"]
    client.post("/api/armed", headers=AUTH, json={"armed": True})
    assert "armed" in ask(client, "is everything ok")["reply"]


def test_jarvis_input_is_checked(client):
    assert client.post("/api/jarvis", headers=AUTH, json={"text": ""}).status_code == 422
    assert client.post("/api/jarvis", headers=AUTH, json={"text": "x" * 500}).status_code == 422
    assert client.post("/api/jarvis", json={"text": "hi"}).status_code == 401
    assert ask(client, "sing me a song")["ok"] is False


def test_jarvis_says_so_when_the_house_cannot_be_reached(client):
    client.hub.publish = lambda *a, **k: False
    r = ask(client, "turn on the light")
    assert r["ok"] is False and "could not reach" in r["reply"]
