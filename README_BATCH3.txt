PHASE 8 - BATCH 3

Adds a fail-closed bridge from an independently validated face identity to the
existing attendance-record model.

Coverage:
- PRESENT + FACE_RECOGNITION marking
- OPEN session enforcement
- student/class authorization
- duplicate protection
- database rollback handling
- rejection of unverified/untrusted identity assertions

The service intentionally does not accept a raw HTTP verified flag and does
not claim that the face-recognition model itself has been validated.
