Phase 8 Batch 2A: offline matching policy and evaluation scaffolding.
No API routes or database schema changed. No real-person accuracy or production threshold established.
Do NOT use CANDIDATE_REVIEW to automatically mark attendance or establish identity.
The values in tests are synthetic examples, not recommended deployment thresholds.
Run: python -m pytest tests/test_face_match_batch2.py -q
Then: python -m pytest -q
Next work: consent-gated candidate retrieval, detector integration, validation data and anti-spoof/manual fallback.
