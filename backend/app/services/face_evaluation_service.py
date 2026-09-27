"""Aggregate offline recognition evaluation; never retain raw biometric vectors."""
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import numpy as np
from backend.app.services.face_match_policy import MatchPolicy, evaluate_candidate


@dataclass(frozen=True)
class EvaluationSummary:
    total: int
    known: int
    unknown: int
    correct_candidates: int
    incorrect_candidates: int
    known_rejected: int
    unknown_candidate_errors: int
    ambiguous: int

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def evaluate_trials(
    trials: Iterable[tuple[int | None, np.ndarray]],
    gallery: Mapping[int, np.ndarray],
    policy: MatchPolicy,
) -> EvaluationSummary:
    """None labels denote non-enrolled probes. Use independent, consented evaluation data."""
    total = known = unknown = correct = incorrect = rejected = false_accept = ambiguous = 0
    for expected, probe in trials:
        if expected is not None and (type(expected) is not int or expected <= 0):
            raise ValueError("Expected label must be a positive integer or None.")
        result = evaluate_candidate(probe, gallery, policy)
        total += 1
        if result.status == "AMBIGUOUS":
            ambiguous += 1
        if expected is None:
            unknown += 1
            if result.candidate_id is not None:
                false_accept += 1
        else:
            known += 1
            if result.candidate_id == expected:
                correct += 1
            elif result.candidate_id is not None:
                incorrect += 1
            else:
                rejected += 1
    return EvaluationSummary(total, known, unknown, correct, incorrect, rejected, false_accept, ambiguous)
