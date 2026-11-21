# Processing Progress and Error States

**PLAGIX v1.0**  
**Last updated:** 21 November 2026

---

## Processing Pipeline States

1. **Queued:** Job waiting for available Celery worker.
2. **Extracting:** Unpacking ZIP, parsing PDF/DOCX/TXT text and preserving offsets.
3. **Checking Relevance:** Evaluating semantic alignment against question and rubric.
4. **Comparing Pairs:** Running N×(N-1)/2 pairwise similarity analysis.
5. **Grading:** Calculating provisional rubric scores.
6. **Ready for Review:** Analysis complete; teacher can inspect results.

---

## Error Handling & Recovery

- **Corrupted / Encrypted Files:** Flagged individually with descriptive error ("File is password protected"); does not fail entire batch.
- **Worker Failure:** Automatic retry with exponential backoff (up to 3 attempts).
- **Retry Actions:** Teachers can retry failed files or continue with successfully extracted submissions.
- **Idempotency:** Retrying extraction or comparison tasks never creates duplicate database records or duplicate pair entries.

---
