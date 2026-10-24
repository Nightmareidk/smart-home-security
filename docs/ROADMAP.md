# Roadmap

## The team

| Track | Who | Works in |
|---|---|---|
| Hardware | 2 computer engineers | `firmware/`, `hardware/` |
| Software | 2 software engineers | `backend/`, `app/`, `ai/`, `simulator/` |
| Molecular | 1 molecular biologist | `molecular/` |

Each track works on its own first. When they are done, the software goes onto the hardware
team's ESP32 boards and we test the finished product together.

The two tracks do not need to wait for each other, because they agree on one contract up front:
the message names and message contents in `docs/ARCHITECTURE.md`. Hardware sends and receives
those messages. Software reads and sends the same messages. If both follow the contract,
joining them is easy.

## What changed since the proposal

- The mold part is a **mold-risk alert** (damp and warm for a set time) in the app, plus the
  molecular student's final experiment, which is separate from the cost list.
- We added plant care, clap light switch, door unlock by fingerprint, face or password,
  "who is home", fire detection and the Jarvis voice assistant.
- All AI runs on a team laptop. There is no Raspberry Pi.
- The finished product has an **app** that controls and shows all of this.

## Software track (the two of us)

Because we do not have the parts yet, a **simulator** pretends to be the boards. It sends fake
sensor readings and reacts to commands, using the same messages the real boards will use.
Everything we build works on the simulator first.

### S0: Setup
- [x] Both clone the repo. Install Python 3.11+ and Node (the message broker for development is built in; Mosquitto comes later).
- [ ] Read `CONTRIBUTING.md` (how we avoid stepping on each other).

### S1: Simulator and server
- [x] `simulator/`: fake door node, plant node and camera, following the contract.
- [x] `backend/`: receives messages, saves them, applies alert rules, sends live updates.

Done when: the simulator's fake readings show up in the server and are saved.

### S2: The app
- [x] `app/`: sensor numbers, alerts, door lock and unlock, lights, plants, armed switch (placeholder look).
- [ ] Check it on a real phone (so far tried in a browser).
- [x] A form where the molecular student enters her final result (detected, not detected, notes).

Done when: pressing "turn on light" in the app makes the simulator react, and the simulator's
mold-risk numbers raise an alert in the app.

### S3: Alert rules
- [x] Mold risk, fire, intrusion, thirsty plant, repeated failed unlocks, board offline.
- [ ] Alert history and a phone notification (Telegram).

### S4: Camera AI (laptop webcam first)
- [ ] `ai/vision/`: people, movement, fire and smoke.
- [ ] `ai/face/`: known faces, "who is home", strangers flagged.
- [ ] Door access log (who, which method, success or fail).

### S5: Jarvis
- [ ] `ai/jarvis/`: wake word, speech to text, language model, spoken replies.
- [ ] Questions first, then control commands, then spoken alerts and scenes.
- [ ] No unlocking by voice alone.

### S6: Join with the hardware (once the boards are ready)
- [ ] Point the server at the real boards instead of the simulator.
- [ ] Switch the camera source to the ESP32-CAM.
- [ ] Fix whatever differs from the contract. Rehearse the demo.

## Hardware track (the two computer engineers)

- [ ] H1: Plant node (ESP32-C3): BME680, soil sensors, pump, lamp, fan, humidifier, clap microphone.
- [ ] H2: Door node (ESP32-S3 T-Display): fingerprint, keypad, lock, buzzer, status screen.
- [ ] H3: Camera node (ESP32-CAM): sends the picture to the laptop.
- [ ] H4: Fill in `hardware/PINS.md`, send and receive the messages in `docs/ARCHITECTURE.md`,
      build the model house.

Done when: each board works alone and speaks the contract. They can test with the same Mosquitto broker.

## Molecular track

- [ ] Her own experiment and write-up in `molecular/`.
- [ ] Her result goes into the app through the lab result form (S2).

## Joining everything

When both tracks finish, we meet, load the software onto the real boards and test the demo
scenes: normal, intruder, known person, fire, clap light, plant watering, mold risk.
