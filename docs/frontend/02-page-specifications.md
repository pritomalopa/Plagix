# Complete Page Specifications

**PLAGIX v1.0**  
**Last updated:** 21 November 2026

---

## Comprehensive Page Inventory (13 Pages)

This document completes all 13 required page specifications for the PLAGIX teacher dashboard.

---

## 1. Login Page (`/login`)
- **Purpose:** Teacher authentication.
- **Fields:** Email, Password, Remember Me.
- **Actions:** Sign In, Forgot Password?, Register link.
- **API:** `POST /api/auth/login`

## 2. Registration Page (`/register`)
- **Purpose:** New teacher account creation and automatic tenant workspace setup.
- **Fields:** Full Name, Institution/School Name, Email, Password, Confirm Password.
- **Actions:** Create Account, Terms of Service agreement checkbox, Sign In link.
- **API:** `POST /api/auth/register`

## 3. Dashboard Page (`/dashboard`)
- **Purpose:** Home view listing all teacher evaluation jobs with status, submission counts, and quick actions.
- **Features:** Search input, status filter (All, Processing, Ready, Completed), sort dropdown, evaluation cards/table.
- **Actions:** [+ New Evaluation], View Results, Delete Evaluation.
- **API:** `GET /api/evaluations`

## 4. Create Evaluation Page (`/evaluations/new`)
- **Purpose:** Multi-step wizard to create an evaluation.
- **Steps:** 
  1. Basic Info (Title, Language, Max Marks, Instructions)
  2. Questions (Prompt, Reference Answer, Expected Concepts, Citation Policy)
  3. Rubric Criteria (Criteria name, description, max points, weight)
  4. Advanced Settings (Similarity thresholds, common content filters)
- **API:** `POST /api/evaluations`

## 5. Edit Evaluation Page (`/evaluations/:id/edit`)
- **Purpose:** Modify evaluation metadata, questions, and rubric before processing begins.
- **Restrictions:** Locked after processing starts (read-only mode with warning).
- **API:** `GET /evaluations/:id`, `PATCH /evaluations/:id`

## 6. Upload Submissions Page (`/evaluations/:id/upload`)
- **Purpose:** Bulk ZIP upload or multi-file dropzone for student answers (PDF, DOCX, TXT).
- **Features:** Drag-and-drop zone, file list with size/status, duplicate hash detection warning, student label mapping review.
- **API:** `POST /api/evaluations/:id/upload`, `POST /api/evaluations/:id/start-processing`

## 7. Processing Status Page (`/evaluations/:id/processing`)
- **Purpose:** Real-time progress view of background Celery workers (extraction → relevance → comparison → grading).
- **Features:** Stage progress bars, estimated time remaining, error details for failed files, [Cancel] / [Retry] actions.
- **API:** `GET /api/evaluations/:id/status`

## 8. Results Dashboard (`/evaluations/:id/results`)
- **Purpose:** Class-level overview of relevance categories and similarity risk flags.
- **Features:** Summary metrics cards, filterable submission table, search by student label, direct links to submission details.
- **API:** `GET /api/evaluations/:id/submissions`

## 9. Individual Submission Detail (`/evaluations/:id/results/submissions/:submissionId`)
- **Purpose:** Detailed inspection of one student's answer, question relevance breakdown, and matched peer passages.
- **Features:** Relevance badge & evidence excerpts, scrollable document viewer with highlights, ranked list of peer matches.
- **API:** `GET /submissions/:id`, `GET /submissions/:id/relevance`, `GET /submissions/:id/comparisons`

## 10. Side-by-Side Comparison Viewer (`/evaluations/:id/results/compare/:subAId/:subBId`)
- **Purpose:** Symmetric pairwise inspection of two student answers.
- **Features:** Canonical pair ordering (`sub_a < sub_b`), exact/lexical/semantic scores, synchronized scrolling, highlighted matching passages.
- **API:** `GET /api/comparisons`, `GET /api/comparisons/:id/passages`

## 11. Teacher Grading and Review (`/evaluations/:id/grading`)
- **Purpose:** Batch review of suggested provisional marks and similarity flags.
- **Features:** Score editing, mandatory override reason modal, flag dismissal, final grade approval.
- **API:** `GET /api/evaluations/:id/grading-results`, `PATCH /api/submissions/:id/grade`

## 12. Reports and Export (`/evaluations/:id/reports`)
- **Purpose:** Generate and download batch summary PDFs, Gradebook CSVs, and individual student report ZIPs.
- **Features:** Format selector, download links with expiration, mandatory SRS plagiarism disclaimer.
- **API:** `POST /api/evaluations/:id/reports`

## 13. Account Settings (`/settings/account`)
- **Purpose:** Teacher profile management, password change, tenant workspace settings, and data retention preferences.
- **Features:** Profile form, security settings, evaluation data deletion controls.
- **API:** `GET /api/users/me`, `PATCH /api/users/me`, `DELETE /api/evaluations/:id`

---
