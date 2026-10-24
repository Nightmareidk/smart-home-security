from app.config import Settings
from app.rules import RuleEngine
from app.state import HomeState


def make(**overrides):
    settings = Settings(mold_hold_seconds=100, **overrides)
    state = HomeState()
    return state, RuleEngine(settings, state)


def feed_env(state, engine, temp, hum, now):
    assert state.apply_env({"temp_c": temp, "humidity": hum}, now)
    return engine.on_env(now)


def test_mold_risk_only_after_the_hold_time():
    state, engine = make()
    assert feed_env(state, engine, 25, 80, 0) == []
    assert feed_env(state, engine, 25, 82, 50) == []
    alerts = feed_env(state, engine, 25, 81, 100)
    assert [a.type for a in alerts] == ["mold_risk"]
    assert alerts[0].severity == "warning" and alerts[0].speak
    assert state.mold_risk
    # no repeat alert while the risk continues
    assert feed_env(state, engine, 25, 85, 200) == []


def test_mold_timer_resets_when_air_gets_dry():
    state, engine = make()
    feed_env(state, engine, 25, 80, 0)
    feed_env(state, engine, 25, 50, 60)  # dry again: timer resets
    assert feed_env(state, engine, 25, 80, 70) == []
    assert feed_env(state, engine, 25, 80, 160) == []  # only 90s since it restarted
    assert [a.type for a in feed_env(state, engine, 25, 80, 171)] == ["mold_risk"]


def test_mold_needs_warm_air_too():
    state, engine = make()
    feed_env(state, engine, 10, 90, 0)  # damp but cold
    assert feed_env(state, engine, 10, 90, 500) == []
    assert not state.mold_risk


def test_mold_fires_from_the_timer_even_without_new_readings():
    state, engine = make()
    feed_env(state, engine, 25, 80, 0)
    assert engine.tick(50) == []
    assert [a.type for a in engine.tick(101)] == ["mold_risk"]


def test_mold_clear_message_when_it_ends():
    state, engine = make()
    feed_env(state, engine, 25, 80, 0)
    engine.tick(101)
    alerts = feed_env(state, engine, 25, 40, 150)
    assert [a.severity for a in alerts] == ["info"]
    assert not state.mold_risk


def test_dry_plant_alert_has_a_cooldown():
    state, engine = make()
    state.apply_soil({"plants": [{"id": 1, "moisture_pct": 10}, {"id": 2, "moisture_pct": 60}]}, 0)
    first = engine.on_soil(0)
    assert [a.data["plant"] for a in first] == [1]
    assert engine.on_soil(10) == []
    assert len(engine.on_soil(400)) == 1


def test_fire_from_flame_sensor_and_from_gas():
    state, engine = make()
    state.apply_fire({"flame": True, "gas_level": 5}, 0)
    assert engine.on_fire_sensor(0)[0].severity == "critical"
    state2, engine2 = make()
    state2.apply_fire({"flame": False, "gas_level": 95}, 0)
    assert engine2.on_fire_sensor(0)[0].type == "fire"
    state3, engine3 = make()
    state3.apply_fire({"flame": False, "gas_level": 10}, 0)
    assert engine3.on_fire_sensor(0) == []


def test_unknown_person_is_an_intrusion_only_when_armed():
    state, engine = make()
    event = {"type": "person", "confidence": 0.9}
    assert engine.on_camera(event, 0)[0].type == "unknown_person"
    state.armed = True
    assert engine.on_camera(event, 100)[0].type == "intrusion"


def test_known_person_is_marked_present_and_gives_no_alert():
    state, engine = make()
    state.armed = True
    assert engine.on_camera({"type": "person", "confidence": 0.95, "name": "sara"}, 5) == []
    assert "sara" in state.people


def test_low_confidence_detections_are_ignored():
    state, engine = make()
    state.armed = True
    assert engine.on_camera({"type": "person", "confidence": 0.2}, 0) == []
    assert engine.on_camera({"type": "fire", "confidence": 0.3}, 0) == []


def test_camera_fire_is_critical():
    state, engine = make()
    alerts = engine.on_camera({"type": "smoke", "confidence": 0.8}, 0)
    assert alerts[0].type == "fire" and alerts[0].severity == "critical"


def test_three_failed_unlocks_raise_an_alert():
    state, engine = make()
    fail = {"method": "keypad", "success": False}
    assert engine.on_access(fail, 0) == []
    assert engine.on_access(fail, 10) == []
    assert engine.on_access(fail, 20)[0].type == "door_failed_attempts"


def test_old_failures_do_not_count():
    state, engine = make()
    fail = {"method": "keypad", "success": False}
    engine.on_access(fail, 0)
    engine.on_access(fail, 10)
    assert engine.on_access(fail, 200) == []


def test_good_unlock_resets_failures_and_marks_user_present():
    state, engine = make()
    fail = {"method": "keypad", "success": False}
    engine.on_access(fail, 0)
    engine.on_access(fail, 1)
    engine.on_access({"method": "fingerprint", "user": "arqam", "success": True}, 2)
    assert engine.on_access(fail, 3) == []
    assert "arqam" in state.people


def test_offline_board_alert():
    state, engine = make()
    assert engine.on_node("plant", False, 0)[0].type == "node_offline"
    assert engine.on_node("plant", True, 1) == []


def test_state_rejects_nonsense_readings():
    state = HomeState()
    assert not state.apply_env({"temp_c": 24, "humidity": 140}, 0)
    assert not state.apply_env({"temp_c": "hot", "humidity": 50}, 0)
    assert not state.apply_env({"temp_c": float("nan"), "humidity": 50}, 0)
    assert not state.apply_env({"temp_c": True, "humidity": 50}, 0)
    assert not state.apply_soil({"plants": "oops"}, 0)
    assert state.apply_env({"temp_c": 24, "humidity": 50}, 0)
