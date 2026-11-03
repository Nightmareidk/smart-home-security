class Confirmer:
    """Turns "seen or not" for every picture into one event per sighting.

    A single picture can be wrong (a coat on a chair looks like a person for a moment), so we
    only report something seen in several pictures in a row, and then wait a little before we
    report it again.
    """

    def __init__(self, frames_needed: int = 3, cooldown: float = 5.0):
        if frames_needed < 1:
            raise ValueError("frames_needed must be at least 1")
        self.frames_needed = frames_needed
        self.cooldown = cooldown
        self._streak = 0
        self._last_event: float | None = None

    def update(self, seen: bool, now: float) -> bool:
        """Call once per picture. True means: report it now."""
        self._streak = self._streak + 1 if seen else 0
        if self._streak < self.frames_needed:
            return False
        if self._last_event is not None and now - self._last_event < self.cooldown:
            return False
        self._last_event = now
        return True
