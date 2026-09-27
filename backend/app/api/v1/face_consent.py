"""Administrative consent endpoints. Evidence verification is an external prerequisite."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.core.dependencies import get_db, require_roles
from backend.app.services.face_consent_service import grant_consent, withdraw_consent

router = APIRouter(prefix="/api/face-consent", tags=["Face consent"])
class ConsentRequest(BaseModel):
    reference: str = Field(min_length=1, max_length=150)

@router.post("/{student_id}")
def record_verified_consent(student_id: int, body: ConsentRequest,
                            db: Session = Depends(get_db), actor=Depends(require_roles("ADMIN"))):
    # The administrator must independently verify informed consent; a reference alone is not proof.
    try:
        result = grant_consent(db, student_id, actor.id, body.reference)
        return {"student_id": result.student_id, "consent_recorded": result.consent_recorded}
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@router.post("/{student_id}/withdraw")
def withdraw(student_id: int, db: Session = Depends(get_db), actor=Depends(require_roles("ADMIN"))):
    try:
        result = withdraw_consent(db, student_id, actor.id)
        return {"student_id": result.student_id, "deletion_pending": result.deletion_pending}
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except OSError as exc:
        raise HTTPException(503, "Deletion pending: storage operation failed; retry required") from exc
