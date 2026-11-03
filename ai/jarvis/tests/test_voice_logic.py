import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alerts import Deduper, clean  # noqa: E402
from endpoint import Endpointer, rms  # noqa: E402
from speech import resample  # noqa: E402


def run(gate, loudness_list):
    for i, loud in enumerate(loudness_list):
        state = gate.update(loud)
        if state != "continue":
            return state, i + 1
    return "continue", len(loudness_list)


def test_done_after_a_short_silence_following_speech():
    gate = Endpointer(noise_level=100)
    state, frames = run(gate, [50] * 5 + [2000] * 15 + [40] * 20)
    assert state == "done"
    assert frames == 5 + 15 + 12  # 0.9 s of quiet is 12 pieces of 80 ms


def test_gives_up_when_nobody_speaks():
    state, _ = run(Endpointer(noise_level=100), [30] * 100)
    assert state == "timeout"


def test_never_records_longer_than_the_limit():
    state, frames = run(Endpointer(noise_level=100, max_seconds=2.0), [3000] * 100)
    assert state == "done" and frames == 25


def test_background_noise_is_not_mistaken_for_speech():
    gate = Endpointer(noise_level=200)  # noisy room: the speech level adapts upwards
    state, _ = run(gate, [400] * 100)
    assert state == "timeout"


def test_loudness():
    assert rms(np.zeros(100, dtype=np.int16)) == 0.0
    assert rms(np.full(100, 1000, dtype=np.int16)) == 1000.0
    assert rms(np.array([], dtype=np.int16)) == 0.0


def test_same_alert_is_not_spoken_twice_in_a_row():
    d = Deduper(20)
    assert d.allow("Fire!", 0) is True
    assert d.allow("Fire!", 5) is False
    assert d.allow("Another one", 6) is True
    assert d.allow("Fire!", 25) is True


def test_only_proper_alert_messages_are_spoken():
    assert clean(b'{"text": "Warning: humidity is high."}') == "Warning: humidity is high."
    assert clean(b'{"text": "   "}') is None
    assert clean(b"not json") is None
    assert clean(b'["a"]') is None
    assert len(clean(b'{"text": "' + b"x" * 500 + b'"}')) == 200


def test_resampling_changes_the_length_only():
    audio = np.arange(22050, dtype=np.int16)
    out = resample(audio, 22050, 16000)
    assert len(out) == 16000 and out.dtype == np.int16
