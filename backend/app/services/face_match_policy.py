"""Conservative face matching for offline evaluation, not attendance authorization.

Thresholds must be calibrated on authorized representative validation data.
No production identity decision is enabled by this module.
"""
from dataclasses import dataclass
from collections.abc import Mapping
import numpy as np


@dataclass(frozen=True)
class MatchPolicy:
    similarity_threshold: float
    ambiguity_margin: float

    def __post_init__(self):
        if not (0.0 < self.similarity_threshold <= 1.0):
            raise ValueError("Similarity threshold must be in (0, 1].")
        if not (0.0 <= self.ambiguity_margin <= 1.0):
            raise ValueError("Ambiguity margin must be in [0, 1].")


@dataclass(frozen=True)
class MatchResult:
    status: str
    candidate_id: int | None
    similarity: float | None
    second_similarity: float | None


def _normalized(vector: np.ndarray) -> np.ndarray:
    if not isinstance(vector, np.ndarray) or vector.shape not in ((128,), (1, 128)):
        raise ValueError("Expected a 128-dimensional NumPy embedding.")
    if vector.dtype != np.float32 or not np.isfinite(vector).all():
        raise ValueError("Embedding must be finite float32.")
    flat = vector.reshape(128).astype(np.float64)
    norm = np.linalg.norm(flat)
    if norm <= 1e-12:
        raise ValueError("Embedding must be nonzero.")
    return flat / norm


def evaluate_candidate(probe: np.ndarray, gallery: Mapping[int, np.ndarray], policy: MatchPolicy) -> MatchResult:
    """Offline candidate ranking. Callers must independently enforce consent and authorization."""
    if not isinstance(policy, MatchPolicy):
        raise TypeError("MatchPolicy required.")
    query = _normalized(probe)
    if not gallery:
        return MatchResult("NO_GALLERY", None, None, None)
    scores = []
    for identifier, reference in gallery.items():
        if type(identifier) is not int or identifier <= 0:
            raise ValueError("Invalid gallery identifier.")
        score = float(np.clip(np.dot(query, _normalized(reference)), -1.0, 1.0))
        scores.append((score, identifier))
    scores.sort(key=lambda item: (-item[0], item[1]))
    top_score, top_id = scores[0]
    second = scores[1][0] if len(scores) > 1 else None
    if top_score < policy.similarity_threshold:
        return MatchResult("BELOW_THRESHOLD", None, top_score, second)
    if second is not None and top_score - second < policy.ambiguity_margin:
        return MatchResult("AMBIGUOUS", None, top_score, second)
    # Candidate only; never treat this as verified attendance identity.
    return MatchResult("CANDIDATE_REVIEW", top_id, top_score, second)
