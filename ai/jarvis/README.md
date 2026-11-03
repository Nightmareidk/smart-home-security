# Jarvis

The house's voice assistant. Say **"Hey Jarvis"**, then a command or a question. Jarvis answers out loud.
**Jarvis never unlocks the door** (the server refuses it as well).

How it fits together:

```
microphone -> wake word ("Hey Jarvis") -> record until you stop -> Whisper (speech to text)
           -> house server  POST /api/jarvis  (backend/app/jarvis.py: understands it, does it, answers)
           -> Piper (text to speech) -> speakers
```

The "brain" lives in the server (`backend/app/jarvis.py`), so typing in the app, typing in a terminal and speaking
all use the same rules. This folder only adds the ears and the voice.

Everything runs **on this laptop**. Nothing is recorded or kept: until it hears the wake word, the microphone sound
is thrown away straight away.

## Set up (once)

```bash
cd ai/jarvis
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python get_models.py       # downloads the speech, voice and wake-word models (about 250 MB, once)
```

## Pick the right microphone and speakers

Windows sometimes chooses a virtual device (for example "Steam Streaming") that has no real sound. List the devices:

```bash
.venv\Scripts\python -m sounddevice
```

Then use the numbers of your real microphone and speakers (on this laptop: microphone 2, speakers 5):

```bash
.venv\Scripts\python voice.py --mic 2 --speaker 5
```

## Run it

```bash
set HOME_API_TOKEN=your-token                   # the same token as the server
.venv\Scripts\python voice.py --mic 2 --speaker 5                 # listens for "Hey Jarvis"
.venv\Scripts\python voice.py --push-to-talk --mic 2 --speaker 5  # press Enter, then speak (no wake word)
.venv\Scripts\python voice.py --file command.wav --no-speak       # understand one recording
.venv\Scripts\python voice.py --say "Hello" --speaker 5           # just speak
.venv\Scripts\python chat.py                                      # typed chat in the terminal
```

Start the house server and message broker first (see `docs/RUNNING.md`).

## What you can say

"Turn on the light" · "Turn off the fan" · "Water the plants" · "Lock the door" · "Arm the system" ·
"What is the temperature?" · "Is there a mold risk?" · "How are the plants?" · "Who is home?" · "Any alerts?" ·
"Is everything okay?" · "Help". Saying "unlock the door" is refused.

## Spoken alerts

While `voice.py` is running, important alerts from the house (fire, intruder, mold risk, door attempts) are spoken
out loud on their own. The same sentence is not repeated within 20 seconds. Use `--no-alerts` to turn this off.

## What was tested, and what was not

| Tested | Not tested yet |
|---|---|
| Spoken test sentences (made by the voice itself) go through Whisper, the server and the simulator, and the house reacts | A real person speaking, in a real room, with background noise |
| The "Hey Jarvis" model reacts to "Hey Jarvis" and not to other phrases (synthetic speech) | The wake word with real voices and accents |
| The microphone opens and reads; speakers play | The whole live loop with a person talking |
| Alerts from the simulator are picked up to be spoken | |

Please try it with real voices and tune `--wake-threshold` (lower = easier to wake, more false wakes) and `--whisper`
(`tiny.en` is faster, `small.en` is more accurate).

## Files

| File | What it does |
|---|---|
| `voice.py` | The program: listens, understands, answers, speaks |
| `speech.py` | Whisper (hear), Piper (speak), the wake word |
| `endpoint.py` | Decides when you have finished speaking (tested) |
| `alerts.py` | Speaks house alerts (tested) |
| `server.py` | Talks to the house server |
| `chat.py` | Typed chat for testing |
| `get_models.py` | Downloads the models |
| `tests/` | `python -m pytest tests` |
