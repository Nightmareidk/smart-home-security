import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from confirm import Confirmer  # noqa: E402


def feed(c, pattern, start=0.0, step=0.5):
    return [c.update(x, start + i * step) for i, x in enumerate(pattern)]


def test_needs_several_pictures_in_a_row():
    assert feed(Confirmer(3, 5), [True, True, False, True, True]) == [False] * 5
    assert feed(Confirmer(3, 5), [True, True, True]) == [False, False, True]


def test_waits_before_reporting_the_same_sighting_again():
    out = feed(Confirmer(frames_needed=2, cooldown=5), [True] * 20, step=0.5)  # 10 seconds of someone standing there
    assert out.count(True) == 2
    assert out[1] is True and out[11] is True


def test_a_gap_starts_the_count_again():
    out = feed(Confirmer(frames_needed=3, cooldown=0), [True, True, False, True, True, True])
    assert out == [False, False, False, False, False, True]


def test_one_picture_is_enough_when_asked():
    assert Confirmer(frames_needed=1, cooldown=0).update(True, 0.0) is True


def test_nothing_seen_never_reports():
    assert not any(feed(Confirmer(2, 1), [False] * 50))


def test_bad_setting_is_refused():
    with pytest.raises(ValueError):
        Confirmer(0)
