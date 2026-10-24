# Architecture

## How the pieces connect

```
 ESP32-CAM  --video-->  Laptop AI (YOLO, face)  --events-->  MQTT broker
 Door node (T-Display S3)  <---- MQTT ---->  Server (Flask + database)  <---->  Dashboard (web page)
 Plant node (C3 Super Mini)  <---- MQTT ---->        ^
                                                     |
 Jarvis (voice) -------------------------------------+
```

- **MQTT** is a message system. Each board sends short messages with a topic name (like a mailbox label).
  Anything that cares about that topic receives it.
- **The server** listens to all messages, saves them in a database, applies the alert rules and
  pushes updates to the dashboard.
- **The AI programs** run on the laptop and talk to the server through the same messages.

## Devices

| Device | Job |
|---|---|
| ESP32-S3 T-Display (owned) | Door node: fingerprint, keypad, lock, buzzer, status screen |
| ESP32-C3 Super Mini (owned) | Plant node: BME680, soil sensors, pump, grow light, humidifier, fan, clap microphone |
| ESP32-CAM | Camera for the door and room |
| Laptop | Server, database, dashboard, camera AI, face recognition, Jarvis |

## Message names (draft)

| Topic | Sent by | Example content |
|---|---|---|
| `home/env/bathroom` | plant node | temperature, humidity, air quality |
| `home/plant/soil` | plant node | soil moisture per plant |
| `home/plant/pump/command` | server or Jarvis | on or off |
| `home/light/command` | server, Jarvis or clap | on, off or toggle |
| `home/fan/command` | server or Jarvis | on or off |
| `home/door/state` | door node | locked or unlocked |
| `home/door/command` | server | lock or unlock |
| `home/door/access` | door node | who tried, which method, success or fail |
| `home/camera/event` | laptop AI | person, movement or fire, with confidence |
| `home/security/armed` | server | true or false |
| `home/alert` | server | type, message, time, snapshot |
| `home/jarvis/say` | server | text for Jarvis to speak |

## Alert rules (draft)

| Alert | Rule |
|---|---|
| Intrusion | System armed, person seen near the door or inside, not a known face |
| Fire | Camera sees fire or smoke, or the flame sensor trips, or gas rises sharply |
| Mold risk | Humidity above about 70% and temperature between 20 and 30 C for a set time (a few minutes in the demo) |
| Thirsty plant | Soil moisture under the limit |
| Door | Unlock attempts that fail repeatedly |

## Tools we plan to use

| Part | Tool |
|---|---|
| Boards | Arduino IDE, C++ |
| Messages | Mosquitto (MQTT) |
| Server | Python, Flask, SQLite |
| Dashboard | A web page served by the server, updated live |
| Camera AI | Python, OpenCV, YOLO |
| Faces | A Python face recognition library |
| Jarvis | Whisper (speech to text), a language model, Piper (voice) |

All are free.
