import numpy as np


def rms(samples: np.ndarray) -> float:
    """How loud a short piece of audio is."""
    if len(samples) == 0:
        return 0.0
    x = samples.astype(np.float32)
    return float(np.sqrt(np.mean(x * x)))


class Endpointer:
    """Decides when you have finished speaking.

    Feed it the loudness of each short piece of audio (80 ms). It waits for speech to start, then says
    "done" after a short silence. If nothing is said for a few seconds it says "timeout", and it never
    records for longer than max_seconds.
    """

    def __init__(self, frame_seconds: float = 0.08, noise_level: float = 150.0, start_factor: float = 3.0,
                 min_loudness: float = 350.0, silence_seconds: float = 0.9, wait_seconds: float = 3.5, max_seconds: float = 8.0):
        self.frame = frame_seconds
        self.threshold = max(min_loudness, noise_level * start_factor)
        self.silence_limit = silence_seconds
        self.wait_limit = wait_seconds
        self.max_limit = max_seconds
        self.elapsed = 0.0
        self.quiet_for = 0.0
        self.speech_started = False

    def update(self, loudness: float) -> str:
        """Returns "continue", "done" or "timeout"."""
        self.elapsed += self.frame
        if loudness >= self.threshold:
            self.speech_started = True
            self.quiet_for = 0.0
        else:
            self.quiet_for += self.frame
        if self.elapsed >= self.max_limit:
            return "done" if self.speech_started else "timeout"
        if self.speech_started and self.quiet_for >= self.silence_limit:
            return "done"
        if not self.speech_started and self.elapsed >= self.wait_limit:
            return "timeout"
        return "continue"
