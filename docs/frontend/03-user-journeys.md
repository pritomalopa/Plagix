# User Journeys and Workflows

**PLAGIX v1.0**  
**Last updated:** 21 November 2026

---

## End-to-End Workflow

The primary user journey for a teacher evaluating student assignments follows this strict sequence:

```
1. Teacher Login
   ↓
2. Create Evaluation Job (Title, Max Marks, Language)
   ↓
3. Enter Question(s) & Optional Rubric / Reference Answer
   ↓
4. Upload Submissions (ZIP bundle or individual PDF/DOCX/TXT files)
   ↓
5. File Validation & Safe Extraction (Malicious check, hash deduplication)
   ↓
6. Answer Relevance Analysis (Evaluated FIRST against question)
   ↓
7. Pairwise Plagiarism Comparison (N × (N-1) / 2 unique pairs)
   ↓
8. Provisional Mark Generation (Rubric-based content scoring)
   ↓
9. Teacher Review & Override (Inspect evidence, edit marks, record reasons)
   ↓
10. Final Grade Approval & Report Export (PDF summary, CSV gradebook, ZIP student reports)
```

---

## Detailed Journey Steps

### Step 1: Authentication
- Teacher navigates to `/login`, enters credentials.
- Upon success, JWT token stored in httpOnly cookie, redirected to `/dashboard`.
- If new user, registers at `/register` which provisions a new tenant workspace automatically.

### Step 2-3: Evaluation Setup
- Teacher clicks [+ New Evaluation] on dashboard.
- Fills out title, language, max marks.
- Adds question prompt, optional reference answer, and rubric criteria (points, weight, expectations).
- Saves evaluation (status: `created`).

### Step 4-5: Ingestion & Upload
- Teacher navigates to upload tab.
- Drag-and-drops a class ZIP archive containing 50 student PDFs plus 3 individual DOCX files.
- System validates file signatures and MIME types, extracts ZIP safely (defending against path traversal and ZIP bombs), and computes SHA-256 hashes to detect duplicates.
- Teacher reviews derived student labels from filenames.

### Step 6-8: Background Processing & Analysis
- Teacher clicks [Start Processing]. Status changes to `processing`.
- Background workers execute pipeline:
  1. **Document Extraction:** Text extracted from PDF/DOCX/TXT with page/offset preservation.
  2. **Relevance Analysis:** Each answer evaluated against the question (Relevant, Partially Relevant, Off-topic, Uncertain).
  3. **Pairwise Comparison:** Unique pairs compared using Winnowing fingerprints, TF-IDF cosine, and semantic embeddings. Matched passages stored.
  4. **Provisional Grading:** Rubric criteria scored based on relevance and content alignment.

### Step 9: Teacher Review & Override
- Processing completes (`ready_for_review`). Teacher opens `/evaluations/:id/results`.
- Teacher filters by high similarity (`>60% lexical match`).
- Clicks on flagged student, inspects side-by-side comparison with matched passage excerpts.
- Realizes matched text is a properly cited definition. Dismisses flag and approves mark.
- For another student with off-topic answer, overrides provisional score from 70 to 0 with required reason: *"Did not answer prompt."*

### Step 10: Export & Completion
- Teacher approves final class grades.
- Generates batch PDF summary and downloads CSV gradebook for import into external systems.
- Evaluation status updated to `completed`.

---
