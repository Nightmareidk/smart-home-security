"""Hearing and speaking: speech to text (Whisper), text to speech (Piper), and the wake word."""
import threading
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MODELS = HERE / "models"
VOICE = MODELS / "piper" / "en_US-lessac-medium.onnx"
SAMPLE_RATE = 16000


def resample(audio: np.ndarray, from_rate: int, to_rate: int = SAMPLE_RATE) -> np.ndarray:
    if from_rate == to_rate:
        return audio
    n = int(len(audio) * to_rate / from_rate)
    return np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio.astype(np.float32)).astype(audio.dtype)


class Transcriber:
    """Speech to text with Whisper, on this laptop. English by default."""

    def __init__(self, size: str = "base.en"):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(size, device="cpu", compute_type="int8", download_root=str(MODELS / "whisper"))

    def transcribe(self, audio_int16: np.ndarray) -> str:
        audio = audio_int16.astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(audio, language="en", beam_size=1, vad_filter=True, condition_on_previous_text=False)
        return " ".join(s.text.strip() for s in segments).strip()


class Speaker:
    """Text to speech with Piper. Only one thing is spoken at a time."""

    def __init__(self, voice_path: Path = VOICE, device: int | None = None):
        from piper import PiperVoice

        self.device = device
        if not voice_path.exists():
            raise SystemExit(f"Missing voice: {voice_path.name}. Run:  python get_models.py")
        self.voice = PiperVoice.load(str(voice_path))
        self.lock = threading.Lock()

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        chunks = [c.audio_int16_array for c in self.voice.synthesize(text)]
        audio = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.int16)
        return audio, self.voice.config.sample_rate

    def speak(self, text: str) -> None:
        import sounddevice as sd

        audio, rate = self.synth(text)
        with self.lock:
            sd.play(audio, rate, device=self.device)
            sd.wait()

    def save(self, text: str, path: Path) -> None:
        import wave

        audio, rate = self.synth(text)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(audio.tobytes())


class WakeWord:
    """Listens for "Hey Jarvis" in 80 ms pieces of 16 kHz audio. Nothing is stored."""

    def __init__(self, threshold: float = 0.5):
        from openwakeword.model import Model

        folder = MODELS / "wake"
        files = sorted(folder.glob("hey_jarvis*.onnx"))
        if not files:
            raise SystemExit("Missing the wake-word model. Run:  python get_models.py")
        self.model = Model(
            wakeword_models=[str(files[0])],
            inference_framework="onnx",
            melspec_model_path=str(folder / "melspectrogram.onnx"),
            embedding_model_path=str(folder / "embedding_model.onnx"),
        )
        self.name = next(iter(self.model.models))
        self.threshold = threshold

    def heard(self, chunk_int16: np.ndarray) -> bool:
        scores = self.model.predict(chunk_int16)
        return scores.get(self.name, 0.0) >= self.threshold

    def reset(self) -> None:
        self.model.reset()
