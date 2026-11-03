"""Jarvis, with a voice. Say "Hey Jarvis", then a command or a question. Jarvis answers out loud.

    python voice.py                          listen for "Hey Jarvis" all the time
    python voice.py --push-to-talk           press Enter, then speak (no wake word)
    python voice.py --file command.wav       understand one recording, then exit
    python voice.py --say "Hello there"      just speak a sentence
    python voice.py --no-speak               print answers instead of speaking

Nothing is recorded or kept. Until it hears the wake word, the microphone sound is thrown away straight away.
Jarvis never unlocks the door (the server refuses it too).
"""
import argparse
import logging
import os
import wave
from collections import deque

import numpy as np

from endpoint import Endpointer, rms
from server import ask
from speech import SAMPLE_RATE, Speaker, Transcriber, WakeWord, resample

log = logging.getLogger("jarvis")
BLOCK = 1280  # 80 ms at 16 kHz


def load_wav(path: str) -> np.ndarray:
    with wave.open(path, "rb") as w:
        rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        if width != 2:
            raise SystemExit("Please use a 16-bit wav file.")
        audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1).astype(np.int16)
    return resample(audio, rate, SAMPLE_RATE)


def chime(sd, device=None):
    t = np.linspace(0, 0.12, int(16000 * 0.12), endpoint=False)
    sd.play((np.sin(2 * np.pi * 880 * t) * 0.25 * 32767).astype(np.int16), 16000, device=device)
    sd.wait()


def record_command(stream, noise_level: float) -> np.ndarray:
    gate = Endpointer(noise_level=noise_level)
    frames = []
    while True:
        block, _ = stream.read(BLOCK)
        chunk = block[:, 0]
        frames.append(chunk)
        state = gate.update(rms(chunk))
        if state != "continue":
            break
    return np.concatenate(frames) if gate.speech_started else np.zeros(0, dtype=np.int16)


def handle(args, transcriber, say, audio: np.ndarray) -> None:
    if len(audio) < SAMPLE_RATE * 0.3:
        say("Sorry, I did not hear anything.")
        return
    text = transcriber.transcribe(audio)
    print(f"  you said: {text or '(nothing clear)'}")
    if not text:
        say("Sorry, I did not catch that.")
        return
    reply = ask(args.server, args.token, text)
    print(f"  Jarvis:   {reply}")
    say(reply)


def warn_about_virtual_devices(args):
    """Windows sometimes picks a virtual device (like Steam Streaming) that has no real sound."""
    import sounddevice as sd

    for kind, chosen, flag in (("input", args.mic, "--mic"), ("output", args.speaker, "--speaker")):
        if chosen is None:
            name = sd.query_devices(kind=kind)["name"]
            if "streaming" in name.lower() or "virtual" in name.lower():
                print(f"Heads up: your default {kind} is '{name}', which may be silent. Run 'python -m sounddevice' and pick a real one with {flag} NUMBER.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--server", default="http://localhost:8000")
    p.add_argument("--token", default=os.environ.get("HOME_API_TOKEN", ""))
    p.add_argument("--host", default="localhost", help="message broker address (for spoken alerts)")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--whisper", default="base.en", help="speech model size: tiny.en, base.en, small.en")
    p.add_argument("--wake-threshold", type=float, default=0.5)
    p.add_argument("--mic", type=int, default=None, help="microphone number (python -m sounddevice lists them)")
    p.add_argument("--speaker", type=int, default=None, help="speaker number (python -m sounddevice lists them)")
    p.add_argument("--push-to-talk", action="store_true")
    p.add_argument("--file")
    p.add_argument("--say")
    p.add_argument("--no-speak", action="store_true")
    p.add_argument("--no-alerts", action="store_true", help="do not speak house alerts")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    warn_about_virtual_devices(args)
    speaker = None if args.no_speak else Speaker(device=args.speaker)

    def say(text: str):
        if speaker:
            speaker.speak(text)

    if args.say:
        say(args.say) if speaker else print(args.say)
        return
    if not args.token:
        raise SystemExit("Set HOME_API_TOKEN (the house server token), or use --token.")

    transcriber = Transcriber(args.whisper)
    if args.file:
        handle(args, transcriber, say, load_wav(args.file))
        return

    import sounddevice as sd

    wake = None if args.push_to_talk else WakeWord(args.wake_threshold)
    listener = None
    if speaker and not args.no_alerts:
        from alerts import AlertListener

        listener = AlertListener(args.host, args.port, speaker.speak)
    recent = deque(maxlen=25)  # loudness of the last two seconds, to know the room's background noise
    print("Ready. Say 'Hey Jarvis'." if wake else "Ready. Press Enter and speak.")
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=BLOCK, device=args.mic) as stream:
            while True:
                if wake:
                    block, _ = stream.read(BLOCK)
                    chunk = block[:, 0]
                    recent.append(rms(chunk))
                    if not wake.heard(chunk):
                        continue
                    print("Hey Jarvis heard. Listening...")
                    chime(sd, args.speaker)
                else:
                    input("\nPress Enter, then speak... ")
                noise = float(np.percentile(recent, 20)) if recent else 150.0
                audio = record_command(stream, noise)
                handle(args, transcriber, say, audio)
                if wake:
                    wake.reset()
                stream.read(stream.read_available)  # throw away what the microphone heard while Jarvis was talking
                recent.clear()
    except KeyboardInterrupt:
        print("\nBye.")
    finally:
        if listener:
            listener.close()


if __name__ == "__main__":
    main()
