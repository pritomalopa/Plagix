# Submission Detail and Comparison Specifications

**PLAGIX v1.0**  
**Last updated:** 21 November 2026

---

## 7. Submission Detail Page (`/evaluations/:id/results/submissions/:submissionId`)

### Purpose
Deep dive into an individual student's submission, showing answer text, relevance evidence, and top peer similarity matches.

### Layout
```
┌────────────────────────────────────────────────────────┐
│ ← Back to Results                                      │
│ Alice Johnson - Midterm Exam                           │
├────────────────────────────────────────────────────────┤
│ [Tab: Answer & Relevance] [Tab: Similarity Matches (3)]│
│                                                        │
│ ┌─ Question Relevance ──────────────────────────────┐  │
│ │ Status: Relevant (Confidence: 92%)                │  │
│ │ Rationale: Answer correctly addresses prompt.     │  │
│ │ Excerpt: "The primary mechanism of photosynthesis..." │  │
│ └───────────────────────────────────────────────────┘  │
│                                                         │
│ ┌─ Answer Document Preview ─────────────────────────┐  │
│ │ Page 1 / 3                                        │  │
│ │ [PDF/Text Viewer with highlighted evidence]       │  │
│ └───────────────────────────────────────────────────┘  │
│                                                         │
│ ┌─ Top Peer Matches ────────────────────────────────┐  │
│ │ 1. Bob Smith — 78% Lexical Match                 │  │
│ │    Matched passage: "Chlorophyll absorbs light..."│  │
│ │    [View Side-by-Side Comparison]                 │  │
│ └───────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### Key Components
1. **Relevance Badge & Rationale**
   - Color-coded category badge
   - Confidence score percentage
   - AI/Rule-based rationale explanation
   - Teacher override option for relevance classification

2. **Document Viewer**
   - Scrollable text / PDF preview
   - Highlighted evidence excerpts
   - Page and paragraph indicators

3. **Matched Peers List**
   - Ordered by similarity strength
   - Shows peer name, match percentage, and match type (exact, lexical, semantic)
   - [Compare] action button leading to side-by-side view

### API Calls
```typescript
GET /api/submissions/:id
GET /api/submissions/:id/relevance
GET /api/submissions/:id/comparisons
```

---

## 8. Side-by-Side Comparison Viewer (`/evaluations/:id/results/compare/:subAId/:subBId`)

### Purpose
Compare two submissions side-by-side with synchronized scrolling and highlighted matching passages.

### Layout
```
┌────────────────────────────────────────────────────────┐
│ ← Back to Submission Detail                            │
│ Comparison: Alice Johnson vs. Bob Smith               │
│ Exact: 15% | Lexical: 78% | Semantic: 91%             │
├──────────────────────────┬─────────────────────────────┤
│ Alice Johnson (Sub A)    │ Bob Smith (Sub B)           │
│ Page 1                   │ Page 1                      │
├──────────────────────────┼─────────────────────────────┤
│ The process of cellular  │ The process of cellular     │
│ respiration converts     │ respiration converts        │
│ glucose into ATP energy  │ glucose into ATP energy     │
│ through glycolysis and   │ through glycolysis and      │
│ oxidative phosphorylation│ oxidative phosphorylation   │
│                          │                             │
│ █ █ █ █ █ █ █ █ █ █ █ █  │ █ █ █ █ █ █ █ █ █ █ █ █     │
│ (Highlighted Match)      │ (Highlighted Match)         │
└──────────────────────────┴─────────────────────────────┘
```

### Key Features
- **Symmetric Display:** A-B comparison (canonical pair order)
- **Multi-Dimension Metrics:** Exact, lexical, and semantic scores shown clearly
- **Synchronized Scrolling:** Scroll one side, other side follows (optional toggle)
- **Highlighted Excerpts:** Matching text blocks highlighted in matching colors
- **Common Content Toggle:** [Hide Question Text] [Hide Boilerplate]

### API Calls
```typescript
GET /api/comparisons?eval_id=&sub_a=&sub_b=
GET /api/comparisons/:id/passages
```

---

## 9. Teacher Review and Grading Page (`/evaluations/:id/grading`)

### Purpose
Batch review provisional marks, override scores, dismiss flags, and finalize grades.

### Layout
```
┌────────────────────────────────────────────────────────┐
│ Midterm Exam - Grading & Review                        │
│ [Results] [Grading] [Reports]                         │
├────────────────────────────────────────────────────────┤
│ Filters: [All Statuses ▾] [Has Flags ▾]                │
│                                                         │
│ Student    Relevance   Flags       Suggested  Final    │
│────────────────────────────────────────────────────────│
│ Alice      Relevant    None        85/100     [ 85 ]   │
│ Bob        Relevant    ⚠ High Sim  72/100     [ 65 ] * │
│ Charlie    Off-topic   None        20/100     [ 0  ] * │
│                                                         │
│ * Modified by teacher (Reason required)               │
│                                                         │
│ [Save Changes] [Approve All Final Grades]             │
└────────────────────────────────────────────────────────┘
```

### Override Workflow
1. Click on provisional mark cell
2. Enter new score
3. Modal pops up: "Reason for Override" (required)
4. Select reason or type custom note
5. Save changes (recorded in audit log)

### Safeguards (SRS Requirements)
- **No Automatic Penalties:** Similarity flags highlight potential issues but do not silently reduce content marks.
- **Audit Trail:** Every override records who changed what, when, and why.
- **Teacher Authority:** Final marks are strictly teacher-approved.

### API Calls
```typescript
GET /api/evaluations/:id/grading-results
PATCH /api/submissions/:id/grade
Request: { teacher_final_score: number, override_reason: string }
```

---

## 10. Reports and Export Page (`/evaluations/:id/reports`)

### Purpose
Generate and download batch summary reports, individual student reports, and CSV exports.

### Layout
```
┌────────────────────────────────────────────────────────┐
│ Midterm Exam - Reports & Export                        │
├────────────────────────────────────────────────────────┤
│ ┌─ Export Options ───────────────────────────────────┐ │
│ │                                                    │ │
│ │ 📄 Batch Summary Report (PDF)                      │ │
│ │    Includes class distribution, flags, and stats.  │ │
│ │    [Download PDF]                                  │ │
│ │                                                    │ │
│ │ 📊 Gradebook Export (CSV)                          │ │
│ │    Compatible with Excel, Google Sheets, LMS.      │ │
│ │    [Download CSV]                                  │ │
│ │                                                    │ │
│ │ 📑 Individual Student Reports (ZIP)                │ │
│ │    Individual PDF reports for all 12 students.     │ │
│ │    [Download ZIP]                                  │ │
│ └───────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

### Export Formats
- **Batch PDF:** Professional summary with charts, statistics, and disclaimers.
- **CSV:** Clean tabular export of student labels, relevance categories, similarity scores, and final grades.
- **Individual PDFs:** One report per student containing relevance evidence, rubric breakdown, and matched peer excerpts.

### Disclaimer Notice
All exported reports include the mandatory SRS disclaimer:
> *"Similarity is an indicator of content overlap and requires human review; it is not automatic proof of plagiarism or academic misconduct."*

### API Calls
```typescript
POST /api/evaluations/:id/reports
Request: { type: 'batch_pdf' | 'csv' | 'individual_zip' }
Response: { download_url: string, expires_at: string }
```

---

## Missing API Endpoints Identified for Frontend

Based on frontend user workflows, the following backend endpoints should be added in future API expansion:

1. **`GET /api/evaluations/{id}/status`** — Polling endpoint for real-time processing progress.
2. **`POST /api/evaluations/{id}/start-processing`** — Trigger background job queue after upload.
3. **`POST /api/evaluations/{id}/cancel`** — Cancel ongoing processing batch.
4. **`GET /api/evaluations/{id}/grading-results`** — Fetch batch grading breakdown.
5. **`GET /api/comparisons`** — Query specific comparison by `sub_a` and `sub_b`.

---

## Summary of Frontend Specification

1. **Architecture:** Next.js App Router + TypeScript + Tailwind CSS + shadcn/ui.
2. **Scope:** Standalone SaaS teacher dashboard (no LMS course management).
3. **Core Flows:** Evaluation creation → ZIP upload → Async processing → Results review → Side-by-side comparison → Grading override → Report export.
4. **Fairness & Safety:** Clear distinction between relevance, similarity, and AI signals; mandatory teacher review and audit trails.

---

## Next Recommended Milestone

**Phase 0.3 Complete.** Ready to begin **Phase 1: MVP Ingestion & API Development** (Backend API implementation for Evaluations CRUD and File Uploads).
