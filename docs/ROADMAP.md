# Roadmap

The order below lets us have something working on screen early, and add hardware one piece at a time.
Each phase ends with something you can demo.

## What changed since the proposal

- No molecular biology or lab work. The mold part is now a **mold-risk alert** (damp and warm
  conditions for a set time), not a DNA test.
- We added plant care, clap light switch, door unlock by fingerprint, face or password,
  "who is home", fire detection and the Jarvis voice assistant.
- All AI runs on a team laptop. There is no Raspberry Pi.

## Phase 0: Set up (day 1)

- [ ] Everyone clones the repo.
- [ ] Install Python 3.11+, the Arduino IDE (with ESP32 support) and Mosquitto (the message broker).
- [ ] Agree the pin map in `hardware/PINS.md` and the message names in `docs/ARCHITECTURE.md`.

## Phase 1: The server and dashboard with fake data (no hardware needed)

- [ ] `backend/`: a small server that receives messages, saves them in a database and sends them to the dashboard live.
- [ ] `dashboard/`: one page with the sensor numbers, alerts list and a "system armed" switch.
- [ ] A script that sends fake temperature and humidity so we can build the screen before the boards are wired.

Done when: fake readings move on the dashboard.

## Phase 2: First real sensor and the mold-risk alert

- [ ] `firmware/plant-node/`: the ESP32-C3 reads the BME680 and sends the numbers.
- [ ] Mold-risk rule in the server: humidity and temperature in the danger zone for a set time raises an alert.
- [ ] Alert shows on the dashboard. The buzzer and fan are added once their relays arrive.

Done when: a humidifier near the sensor makes the dashboard show a mold-risk alert.

## Phase 3: Camera AI

- [ ] `ai/vision/`: start with the laptop webcam. YOLO finds people, then movement, then fire and smoke.
- [ ] Add the ESP32-CAM as the camera source.
- [ ] Events (person detected, fire detected) go to the server with a snapshot.
- [ ] Intrusion rule: door area plus person plus system armed gives an alert.

Done when: walking in front of the camera while armed raises an alert with a photo.

## Phase 4: Door access

- [ ] `firmware/door-node/`: the T-Display S3 reads the fingerprint sensor and keypad and drives the lock.
- [ ] `ai/face/`: face recognition, enrolling people, and the "who is home" list.
- [ ] Every unlock, success or fail, is logged.

Done when: fingerprint, keypad and face can each open the door, and strangers are flagged.

## Phase 5: Plants and clap switch

- [ ] Soil sensors, pump and grow light on a timer in the plant node.
- [ ] Clap detection with the MAX9814 microphone.

Done when: dry soil gets watered by itself, and two claps toggle the light.

## Phase 6: Jarvis

- [ ] `ai/jarvis/`: wake word, speech to text, language model, spoken replies.
- [ ] Start with questions (temperature, who is home), then control commands, then spoken alerts and scenes.
- [ ] Safety rule: no unlocking by voice alone.

Done when: "Jarvis, is there a mold risk?" gets a correct spoken answer.

## Phase 7: Polish and demo

- [ ] Build the model house and place the camera, lock and bathroom corner.
- [ ] Rehearse the demo scenes: normal, intruder, known person, fire, clap light, plant watering, mold risk.
- [ ] Final testing, error handling, and the report.

## Suggested first steps

1. Phase 0 together.
2. One person starts Phase 1 (server and dashboard).
3. One person starts Phase 2 (BME680 and ESP32-C3), since these parts are already owned.
4. One person starts Phase 3 with the webcam, which needs no purchase.
