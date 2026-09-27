"""Fail-closed, offline identity candidate review. No attendance authorization."""
from collections.abc import Mapping
import numpy as np
from sqlalchemy.orm import Session
from backend.app.models.student_face import StudentFace
from backend.app.services.face_match_policy import MatchPolicy, MatchResult, evaluate_candidate


def review_probe(db: Session, probe: np.ndarray, gallery: Mapping[int, np.ndarray],
                 policy: MatchPolicy, face_count: int, alignment_validated: bool = False,
                 threshold_validated: bool = False) -> MatchResult:
    """Review only consented, non-pending enrolled gallery entries.

    Explicit validation flags are fail-closed and MUST only be set after independent
    evaluation; this function never verifies identity or marks attendance.
    """
    if type(face_count) is not int or face_count != 1:
        return MatchResult("REJECT_FACE_COUNT", None, None, None)
    if not alignment_validated or not threshold_validated:
        return MatchResult("VALIDATION_REQUIRED", None, None, None)
    if not gallery:
        return MatchResult("NO_GALLERY", None, None, None)
    # Fetch authoritative DB state, not caller-supplied consent claims.
    permitted = {}
    for student_id, embedding in gallery.items():
        if type(student_id) is not int or student_id <= 0:
            raise ValueError("Invalid student identifier")
        record = db.query(StudentFace).filter_by(student_id=student_id).one_or_none()
        if (record is not None and record.is_enrolled and record.consent_recorded
                and not record.deletion_pending and record.consent_withdrawn_at is None):
            permitted[student_id] = embedding
    if not permitted:
        return MatchResult("NO_CONSENTED_GALLERY", None, None, None)
    return evaluate_candidate(probe, permitted, policy)
