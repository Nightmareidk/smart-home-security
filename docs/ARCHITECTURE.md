# Architecture

## How the pieces connect

```
 ESP32-CAM  --video-->  Laptop AI (YOLO, face)  --events-->  MQTT broker
 Door node (T-Display S3)  <---- MQTT ---->  Server (Flask + database)  <---->  App (web page)
 Plant node (C3 Super Mini)  <---- MQTT ---->        ^
                                                     |
 Jarvis (voice) -------------------------------------+
```

- **MQTT** is a message system. Each board sends short messages with a topic name (like a mailbox label).
  Anything that cares about that topic receives it.
- **The server** listens to all messages, saves them in a database, applies the alert rules and
  pushes updates to the app.
- **The AI programs** run on the laptop and talk to the server through the same messages.

## Devices

| Device | Job |
|---|---|
| ESP32-S3 T-Display | Door node: fingerprint, keypad, lock, buzzer, status screen |
| ESP32-C3 Super Mini | Plant node: BME680, soil sensors, pump, grow light, humidifier, fan, clap microphone |
| ESP32-CAM | Camera for the door and room |
| Laptop | Server, database, app, camera AI, face recognition, Jarvis |

## Messages

The full list of message names and contents, which is the agreement between the hardware and
software teams, is in `docs/CONTRACT.md`.

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
| App | A web page served by the server, updated live |
| Camera AI | Python, OpenCV, YOLO |
| Faces | A Python face recognition library |
| Jarvis | Whisper (speech to text), a language model, Piper (voice) |

All are free.
