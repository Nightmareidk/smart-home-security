import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import best_match, identify, similarity  # noqa: E402
from store import FaceStore, clean_name  # noqa: E402


def vec(*values):
    return np.array(values, dtype=np.float32)


PEOPLE = {
    "sara": [vec(1, 0, 0, 0), vec(0.9, 0.1, 0, 0)],
    "arqam": [vec(0, 1, 0, 0)],
}


def test_same_face_scores_one_and_different_faces_score_low():
    assert similarity(vec(1, 2, 3), vec(2, 4, 6)) == pytest.approx(1.0)
    assert similarity(vec(1, 0), vec(0, 1)) == pytest.approx(0.0)


def test_picks_the_closest_person():
    name, score = best_match(vec(0.95, 0.05, 0, 0), PEOPLE)
    assert name == "sara" and score > 0.99


def test_a_stranger_is_not_named():
    name, score = identify(vec(0, 0, 1, 0), PEOPLE, threshold=0.45)
    assert name is None and score < 0.45


def test_a_close_face_is_named():
    assert identify(vec(0.1, 0.95, 0, 0), PEOPLE, threshold=0.45)[0] == "arqam"


def test_nobody_enrolled_means_everyone_is_a_stranger():
    assert identify(vec(1, 0), {}, 0.45)[0] is None


def test_store_needs_consent_and_can_delete(tmp_path):
    store = FaceStore(tmp_path / "people.json")
    with pytest.raises(ValueError):
        store.add("sara", [vec(1, 0)], consent="")
    store.add("Sara Khan", [vec(1, 0), vec(0.9, 0.1)], can_unlock=True, consent="yes, written")
    assert store.names() == ["sara_khan"] and store.can_unlock("sara_khan")
    again = FaceStore(tmp_path / "people.json")  # survives a restart
    assert len(again.people()["sara_khan"]) == 2
    assert again.delete("sara_khan") is True
    assert FaceStore(tmp_path / "people.json").names() == []
    assert again.delete("nobody") is False


def test_store_keeps_only_numbers_not_photos(tmp_path):
    store = FaceStore(tmp_path / "people.json")
    store.add("sara", [vec(1, 0, 0)], consent="yes")
    text = (tmp_path / "people.json").read_text()
    assert "embeddings" in text and "jpg" not in text and "png" not in text


@pytest.mark.parametrize("bad", ["", "a/b", "../x", "x" * 41, "sa$ra"])
def test_bad_names_are_refused(bad):
    with pytest.raises(ValueError):
        clean_name(bad)
