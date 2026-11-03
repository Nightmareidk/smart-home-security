# Changelog

How versions work is in `CONTRIBUTING.md`. Newest first.

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
