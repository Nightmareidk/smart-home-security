# Changelog

How versions work is in `CONTRIBUTING.md`. Newest first.

## Beta 1.2

- **Face recognition** (`ai/face/`): enrol people (with consent), recognise them on a camera, and report their name. Known people show as Home in the app. Unknown faces raise an intruder alert when the system is armed.
- **Open the door by face** (off by default): only for people enrolled with permission to, with a strict match, several matches in a row, and the `--allow-unlock` switch. Every opening is logged with the method `face` and the name.
- **Fewer false alarms:** an unnamed person seen within 15 seconds of a recognised person is treated as that same person.
- Faces are stored only on the laptop as numbers (not photos), in a folder git ignores. Anyone can be deleted with one command.
- Tests: 70 server tests, 12 face tests, 6 camera AI tests.

## Beta 1.1

- **Jarvis, typed.** The server understands commands and questions ("turn on the fan", "is there a mold risk?", "who is home?") through `POST /api/jarvis`. The app's Jarvis tab is now a chat. Jarvis never unlocks the door.
- **Camera AI version 1** (`ai/vision/`): finds people in a webcam, video or camera stream and reports them. Fire and smoke work once a trained model is given.
- **Door re-lock:** every unlock now carries a time (default 5 seconds, at most 30) and the board locks itself again.
- **Contract:** camera picture addresses, door re-lock time and how claps are reported are written down in `docs/CONTRACT.md`.
- **Simulator:** the pretend door re-locks by itself, and a new `clap` scenario toggles the light.
- Tests: 65 server tests, 6 camera AI tests.
- Screenshots: `screenshots/v1.1/`

## Beta 1.0

The first working version of the software side. Runs fully on the simulator, no hardware needed.

- Message contract between boards, server and app (`docs/CONTRACT.md`)
- Server: live state, saved readings and alerts, alert rules (mold risk, fire, intruder, thirsty plant, failed door attempts, board offline), token protection
- Simulator for the door, plant and camera boards, with test scenarios
- Phone app: Home, Security, Plants, Alerts, Settings, Lab result form; Jarvis tab is a placeholder
- Placeholder look
- Screenshots: `screenshots/v1.0/`
