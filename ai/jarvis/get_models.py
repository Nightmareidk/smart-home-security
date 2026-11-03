"""Downloads the three voice models into the models folder (about 250 MB in total, once).

  - Whisper (speech to text), base.en
  - Piper voice (text to speech), en_US-lessac-medium
  - the "Hey Jarvis" wake-word model (openWakeWord)
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = HERE / "models"


def main():
    MODELS.mkdir(exist_ok=True)
    if not (MODELS / "piper" / "en_US-lessac-medium.onnx").exists():
        print("Piper voice...")
        subprocess.check_call([sys.executable, "-m", "piper.download_voices", "en_US-lessac-medium", "--data-dir", str(MODELS / "piper")])
    if not list((MODELS / "wake").glob("hey_jarvis*.onnx")):
        print("Wake word...")
        import openwakeword.utils as u

        u.download_models(["hey_jarvis"], target_directory=str(MODELS / "wake"))
    print("Whisper (the first time only)...")
    from faster_whisper import WhisperModel

    WhisperModel("base.en", download_root=str(MODELS / "whisper"))
    print("All models are ready.")


if __name__ == "__main__":
    main()
