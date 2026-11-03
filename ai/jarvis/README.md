# Jarvis

The voice assistant. The "brain" (turning a sentence into one allowed action, and the answers) lives in the server:
`backend/app/jarvis.py`, reached by `POST /api/jarvis`. It uses the same safety rules as the app's buttons, and
**Jarvis never unlocks the door**.

## Where we are

| Step | Status |
|---|---|
| J1 Typed commands | **Done.** Type in the app's Jarvis tab, or run `python chat.py` here |
| J2 Speech to text | Next (Whisper) |
| J3 Spoken answers | Next (Piper) |
| J4 Wake word ("Hey Jarvis") | Next |
| J5 Spoken alerts (`home/jarvis/say`) | Next |
| J6 Scenes, greetings, reminders | Later |

The voice program will only do speech to text, call `POST /api/jarvis` with the text, and read the reply out loud.

## Try typing now

```bash
python chat.py            # set HOME_API_TOKEN first, or use --token
```
