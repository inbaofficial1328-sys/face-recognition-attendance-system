import numpy as np
import pytest
from backend.app.services.face_match_policy import MatchPolicy, evaluate_candidate
from backend.app.services.face_evaluation_service import evaluate_trials


def vector(a=1.0, b=0.0):
    result = np.zeros((1, 128), dtype=np.float32)
    result[0, 0] = a
    result[0, 1] = b
    return result


def test_empty_gallery():
    assert evaluate_candidate(vector(), {}, MatchPolicy(.8, .05)).status == "NO_GALLERY"


def test_candidate_requires_review():
    result = evaluate_candidate(vector(), {1: vector(), 2: vector(0, 1)}, MatchPolicy(.8, .05))
    assert (result.status, result.candidate_id) == ("CANDIDATE_REVIEW", 1)


def test_below_threshold():
    result = evaluate_candidate(vector(), {1: vector(0, 1)}, MatchPolicy(.8, .05))
    assert result.status == "BELOW_THRESHOLD" and result.candidate_id is None


def test_ambiguous_candidates():
    result = evaluate_candidate(vector(), {1: vector(), 2: vector()}, MatchPolicy(.8, .05))
    assert result.status == "AMBIGUOUS" and result.candidate_id is None


def test_reject_bad_embeddings_and_thresholds():
    with pytest.raises(ValueError):
        MatchPolicy(0, .05)
    with pytest.raises(ValueError):
        evaluate_candidate(np.zeros((1, 128), np.float32), {1: vector()}, MatchPolicy(.8, .05))
    with pytest.raises(ValueError):
        evaluate_candidate(vector(), {1: np.full((1, 128), np.nan, np.float32)}, MatchPolicy(.8, .05))


def test_offline_evaluation_counts():
    summary = evaluate_trials([(1, vector()), (1, vector(0, 1)), (None, vector(0, 1))],
                              {1: vector()}, MatchPolicy(.8, .05))
    assert summary.total == 3
    assert summary.correct_candidates == 1
    assert summary.known_rejected == 1
    assert summary.unknown_candidate_errors == 0
