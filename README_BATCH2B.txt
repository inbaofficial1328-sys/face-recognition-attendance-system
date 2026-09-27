Phase 8 Batch 2B: local camera face-count preview and consent-gated OFFLINE candidate review.
This does NOT establish identity, enable an endpoint, or mark attendance.
Alignment and thresholds must be validated on authorized representative test data before enabling review.
Run: python -m pytest tests/test_face_batch2b.py -q
Optional local camera preview: python -m scripts.preview_face_camera_batch2b
No biometric vectors or frames are written by the preview.
