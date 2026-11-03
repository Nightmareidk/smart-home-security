import numpy as np


def normalise(vec) -> np.ndarray:
    v = np.asarray(vec, dtype=np.float32).ravel()
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def similarity(a, b) -> float:
    """How alike two faces are, from -1 to 1 (1 means identical). Cosine similarity."""
    return float(np.dot(normalise(a), normalise(b)))


def best_match(embedding, people: dict[str, list]) -> tuple[str | None, float]:
    """Find the enrolled person who looks most like this face. Returns (name, score)."""
    best_name, best_score = None, -1.0
    for name, samples in people.items():
        for sample in samples:
            score = similarity(embedding, sample)
            if score > best_score:
                best_name, best_score = name, score
    return best_name, best_score


def identify(embedding, people: dict[str, list], threshold: float) -> tuple[str | None, float]:
    """Name the face, or None (a stranger) if nobody is alike enough."""
    name, score = best_match(embedding, people)
    return (name, score) if name is not None and score >= threshold else (None, score)
