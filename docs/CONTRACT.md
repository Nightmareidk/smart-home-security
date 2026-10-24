# The contract: messages between boards, server and app

This file is the single agreement between the hardware team and the software team.
If the boards send and receive exactly these messages, everything connects. If you need to
change something, change it here first and tell the other team.

All messages are **MQTT** with a **JSON** body. Times are not sent by the boards; the server
adds its own time when a message arrives.

Rules for everyone:

- Topic names are lowercase and start with `home/`.
- Numbers are plain numbers, not text. Switches are `true` or `false`.
- A board that cannot read a sensor leaves that field out. It never sends made-up values.
- Each board sets a "last will" so the server knows when it goes offline (see Nodes).

## Nodes (is the board alive?)

Topic: `home/node/<name>/status`, retained, sent when the board connects.
The board's last will is the same topic with `offline`.

| Node name | Board |
|---|---|
| `door` | ESP32-S3 T-Display |
| `plant` | ESP32-C3 Super Mini |
| `cam` | ESP32-CAM |

```json
{"online": true}
```

## Sensors (boards send, every 2 to 10 seconds)

| Topic | From | Body |
|---|---|---|
| `home/env/bathroom` | plant | `{"temp_c": 24.3, "humidity": 58.2, "iaq": 80, "pressure_hpa": 1011}` (`iaq` and `pressure_hpa` optional; `iaq` is air quality, 0 bad to 100 good) |
| `home/plant/soil` | plant | `{"plants": [{"id": 1, "moisture_pct": 41}, {"id": 2, "moisture_pct": 18}]}` |
| `home/sensor/fire` | plant | `{"flame": false, "gas_level": 12}` (`gas_level` 0 to 100) |

## Actuators (switches the server or app can control)

Names: `light`, `growlight`, `pump`, `fan`, `humidifier`, `heater`, `buzzer`.

| Topic | From | Body |
|---|---|---|
| `home/actuator/<name>/command` | server | `{"action": "on"}` or `{"action": "off"}`. Optional `"seconds": 10` means turn off by itself after that long (the pump must always have a limit). |
| `home/actuator/<name>/state` | board | `{"on": true}` sent **retained** after every change, and when the board starts |

The board does the switching and confirms with `state`. The server never assumes it worked.
State messages are **retained**, so the server learns the current state straight away when it restarts.

## Door

| Topic | From | Body |
|---|---|---|
| `home/door/command` | server | `{"action": "lock"}` or `{"action": "unlock"}` |
| `home/door/state` | door | `{"locked": true}` sent **retained** after every change, and when the board starts |
| `home/door/access` | door | `{"method": "fingerprint", "user": "sara", "success": true}` for every attempt. `method` is `fingerprint`, `keypad`, `face` or `app`. `user` is left out when unknown. |

## Camera and AI (the laptop sends these)

Topic: `home/camera/event`

```json
{"type": "person", "confidence": 0.91, "name": "sara", "snapshot": "snapshots/2026-10-24T10-00-00.jpg"}
```

- `type`: `person`, `movement`, `fire`, `smoke` or `face`
- `name`: who the face belongs to. Left out or `null` means a stranger.
- `snapshot`: optional file name of the picture

## Security state (the server owns this)

| Topic | From | Body |
|---|---|---|
| `home/security/armed` | server, retained | `{"armed": true}` (boards show it on their screens) |
| `home/alert` | server | `{"id": 7, "type": "mold_risk", "severity": "warning", "message": "...", "ts": 1761300000}` |
| `home/jarvis/say` | server | `{"text": "Warning, humidity has been high for two minutes."}` |

`severity` is `info`, `warning` or `critical`.

## Alert types

`mold_risk`, `fire`, `intrusion`, `unknown_person`, `plant_dry`, `door_failed_attempts`, `node_offline`.

## Testing without the real boards

`simulator/sim.py` speaks this contract and pretends to be all three boards. Hardware can use
it as the reference for what the server expects.
