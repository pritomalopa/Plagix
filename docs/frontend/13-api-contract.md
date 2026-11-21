# Frontend-to-Backend API Contract

**PLAGIX v1.0**  
**Last updated:** 21 November 2026

---

## API Status & Endpoint Inventory

This document defines the API contract between the Next.js frontend and the FastAPI backend.

### Existing Backend Endpoints (Phase 0.2 Implemented)
- `GET /health/live` — Liveness check
- `GET /health/ready` — Readiness check (DB & Redis)
- `GET /` — Root API info

### Required Backend Endpoints (To Be Implemented in Phase 1+)
1. **Authentication:**
   - `POST /api/auth/register` — Teacher account creation
   - `POST /api/auth/login` — JWT token generation
   - `POST /api/auth/logout` — Session termination
2. **Evaluations CRUD:**
   - `GET /api/evaluations` — List tenant evaluations
   - `POST /api/evaluations` — Create new evaluation
   - `GET /api/evaluations/{id}` — Evaluation details
   - `PATCH /api/evaluations/{id}` — Update evaluation
   - `DELETE /api/evaluations/{id}` — Delete evaluation and files
3. **Upload & Processing:**
   - `POST /api/evaluations/{id}/upload` — Multipart file/ZIP upload
   - `POST /api/evaluations/{id}/start-processing` — Enqueue background tasks
   - `GET /api/evaluations/{id}/status` — Polling job progress
   - `POST /api/evaluations/{id}/cancel` — Cancel processing batch
4. **Results & Analysis:**
   - `GET /api/evaluations/{id}/submissions` — List submissions with relevance & similarity
   - `GET /api/submissions/{id}` — Individual submission details
   - `GET /api/submissions/{id}/relevance` — Relevance evidence
   - `GET /api/comparisons` — Pairwise comparison lookup
   - `GET /api/comparisons/{id}/passages` — Matched text excerpts
5. **Grading & Reports:**
   - `GET /api/evaluations/{id}/grading-results` — Batch grading summary
   - `PATCH /api/submissions/{id}/grade` — Teacher mark override & audit
   - `POST /api/evaluations/{id}/reports` — Generate PDF/CSV/ZIP reports

---
