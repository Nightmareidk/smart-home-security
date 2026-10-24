import json
import os

os.environ["HOME_MQTT_ENABLED"] = "false"
os.environ["HOME_DB_PATH"] = ":memory:"
os.environ["HOME_API_TOKEN"] = "test-token"
os.environ["HOME_MOLD_HOLD_SECONDS"] = "0"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        hub = app.state.hub
        published = []
        hub.publish = lambda topic, payload, retain=False: published.append((topic, payload)) or True
        c.published = published
        c.hub = hub
        yield c


def send(client, topic, payload):
    """Feed a fake MQTT message to the server, the way the broker would."""
    client.portal.call(client.hub.handle_message, topic, json.dumps(payload).encode())


def test_health_is_open_but_everything_else_needs_the_token(client):
    assert client.get("/api/health").json()["ok"] is True
    assert client.get("/api/state").status_code == 401
    assert client.get("/api/state", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/api/state", headers=AUTH).status_code == 200


def test_sensor_message_shows_up_in_state_and_history(client):
    send(client, "home/env/bathroom", {"temp_c": 24.5, "humidity": 55})
    state = client.get("/api/state", headers=AUTH).json()
    assert state["env"]["humidity"] == 55
    rows = client.get("/api/readings/humidity", headers=AUTH).json()
    assert rows and rows[-1]["value"] == 55


def test_bad_messages_are_ignored(client):
    send(client, "home/env/bathroom", {"temp_c": 24.5, "humidity": 900})
    client.portal.call(client.hub.handle_message, "home/env/bathroom", b"not json")
    client.portal.call(client.hub.handle_message, "home/env/bathroom", b"[1,2]")
    assert client.get("/api/state", headers=AUTH).json()["env"] == {}


def test_mold_alert_reaches_the_alert_list_and_jarvis(client):
    send(client, "home/env/bathroom", {"temp_c": 26, "humidity": 85})
    send(client, "home/env/bathroom", {"temp_c": 26, "humidity": 86})
    alerts = client.get("/api/alerts", headers=AUTH).json()
    assert any(a["type"] == "mold_risk" for a in alerts)
    topics = [t for t, _ in client.published]
    assert "home/alert" in topics and "home/jarvis/say" in topics


def test_actuator_command_is_published(client):
    r = client.post("/api/actuators/light", headers=AUTH, json={"action": "on"})
    assert r.status_code == 200
    assert ("home/actuator/light/command", {"action": "on"}) in client.published


def test_pump_always_gets_a_time_limit(client):
    client.post("/api/actuators/pump", headers=AUTH, json={"action": "on"})
    topic, payload = client.published[-1]
    assert payload["seconds"] == 10
    client.post("/api/actuators/pump", headers=AUTH, json={"action": "on", "seconds": 500})
    assert client.published[-1][1]["seconds"] == 60


def test_unknown_device_and_bad_input_are_rejected(client):
    assert client.post("/api/actuators/toaster", headers=AUTH, json={"action": "on"}).status_code == 422
    assert client.post("/api/actuators/light", headers=AUTH, json={"action": "explode"}).status_code == 422
    assert client.post("/api/actuators/light", headers=AUTH, json={"action": "on", "extra": 1}).status_code == 422


def test_door_cannot_be_unlocked_by_voice(client):
    r = client.post("/api/door", headers=AUTH, json={"action": "unlock", "source": "voice"})
    assert r.status_code == 403
    assert not any(t == "home/door/command" for t, _ in client.published)
    assert client.post("/api/door", headers=AUTH, json={"action": "lock", "source": "voice"}).status_code == 200
    assert client.post("/api/door", headers=AUTH, json={"action": "unlock", "source": "app"}).status_code == 200


def test_commands_fail_cleanly_when_the_broker_is_down(client):
    client.hub.publish = lambda *a, **k: False
    assert client.post("/api/actuators/light", headers=AUTH, json={"action": "on"}).status_code == 503


def test_arming_is_saved_and_shared(client):
    assert client.post("/api/armed", headers=AUTH, json={"armed": True}).status_code == 200
    assert client.get("/api/state", headers=AUTH).json()["armed"] is True
    assert ("home/security/armed", {"armed": True}) in client.published


def test_intruder_when_armed(client):
    client.post("/api/armed", headers=AUTH, json={"armed": True})
    send(client, "home/camera/event", {"type": "person", "confidence": 0.9})
    alerts = client.get("/api/alerts", headers=AUTH).json()
    assert alerts[0]["type"] == "intrusion"
    assert client.post(f"/api/alerts/{alerts[0]['id']}/ack", headers=AUTH).status_code == 200
    assert client.get("/api/alerts?open=true", headers=AUTH).json() == []


def test_lab_result_form(client):
    body = {"result": "detected", "target": "Aspergillus ITS", "notes": "Band at 550 bp", "author": "lab"}
    assert client.post("/api/lab-results", headers=AUTH, json=body).status_code == 201
    assert client.get("/api/lab-results", headers=AUTH).json()[0]["target"] == "Aspergillus ITS"
    assert client.post("/api/lab-results", headers=AUTH, json={**body, "result": "maybe"}).status_code == 422


def test_bad_metric_name_is_refused(client):
    assert client.get("/api/readings/humidity;drop", headers=AUTH).status_code in (400, 404)


def test_websocket_needs_the_token_and_sends_state(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws?token=wrong"):
            pass
    with client.websocket_connect("/ws?token=test-token") as ws:
        assert ws.receive_json()["type"] == "state"
