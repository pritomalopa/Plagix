# PLAGIX Planning Session Summary

**Date:** 16 November 2026  
**Session Type:** Phase 0 Planning (Architecture & Requirements)  
**Status:** Planning Complete — Ready for Implementation

---

## 1. Architecture Summary

### Selected Architecture

**Modular Monolith** with clear internal boundaries:

- **Frontend:** Next.js 14+ with TypeScript, Tailwind CSS, shadcn/ui
- **Backend API:** Python 3.11+ with FastAPI, Pydantic validation
- **Database:** PostgreSQL 15+ with pgvector (Phase 4)
- **Background Jobs:** Redis + Celery for async processing
- **Document Processing:** PyMuPDF, python-docx
- **NLP/Analysis:** scikit-learn (TF-IDF), sentence-transformers (multilingual embeddings)
- **Object Storage:** S3-compatible (Cloudflare R2 candidate for zero egress fees)
- **Containerization:** Docker + Docker Compose for reproducible environments

### Key Architectural Decisions

1. **Canonical Pair Storage:** Store exactly one record per unordered submission pair with `submission_a_id < submission_b_id` and database unique constraint on `(evaluation_id, submission_a_id, submission_b_id)` to ensure A-B and B-A resolve to the same result.

2. **Relevance-First Pipeline:** Question relevance analysis MUST complete before pairwise similarity comparison begins (enforced by state machine).

3. **Separate Similarity Dimensions:** Exact, lexical, and semantic similarity kept distinct; never merged into single opaque percentage.

4. **Local NLP Models:** Use sentence-transformers locally to avoid per-request API costs, maintain privacy, and ensure offline capability. External AI APIs deferred to Phase 4 with explicit teacher consent.

5. **Safe File Handling:** Multi-layer validation (MIME checks, ZIP bomb detection, path traversal prevention, malware scanning) at ingestion stage.

6. **Tenant Isolation:** Enforced at API middleware, database queries, and object storage key prefixes with foreign key cascades and authorization checks.

---

## 2. Documents Created (Checklist vs. SRS)

| Document | SRS Requirement | Status | Location |
|----------|----------------|--------|----------|
| **README.md** | Product summary, scope, stack | ✅ Complete | `/README.md` |
| **Requirements Traceability** | FR mapping to modules, tests, phases | ✅ Complete | `/docs/requirements/requirements-traceability.md` |
| **System Overview** | Components, workflow, Mermaid diagrams | ✅ Complete | `/docs/architecture/system-overview.md` |
| **Data Model** | Entities, relationships, canonical pair storage | ✅ Complete | `/docs/architecture/data-model.md` |
| **Processing Pipeline** | Upload → extraction → analysis → grading flow | ✅ Complete | `/docs/architecture/processing-pipeline.md` |
| **ADR-0001: Technology Stack** | Stack rationale and trade-offs | ✅ Complete | `/docs/decisions/ADR-0001-technology-stack.md` |
| **Phase Plan** | Testable milestones from foundation to SaaS | ✅ Complete | `/docs/roadmap/phase-plan.md` |
| **Open Questions** | Unresolved decisions with recommendations | ✅ Complete | `/docs/open-questions.md` |

### SRS Mapping Validation

All planning artifacts trace back to SRS v1.0:
- ✅ 28 functional requirements (FR-01 to FR-28) mapped to modules and phases
- ✅ 10 non-functional requirements (NFR-01 to NFR-10) mapped to implementation approach
- ✅ 14 acceptance criteria (AC-01 to AC-14) mapped to test phases
- ✅ All fairness rules, safety constraints, and workflow requirements incorporated
- ✅ Explicit handling of canonical pair storage, relevance-first evaluation, and teacher oversight

---

## 3. SRS Ambiguities and Recommendations

### Resolved by Planning

| SRS Area | Ambiguity | Resolution |
|----------|-----------|------------|
| **File limits** | Maximum ZIP/file size not specified | Recommended: 250MB ZIP, 50MB file, 500 count (configurable, validate in Phase 1) |
| **Student mapping** | Filename parsing conventions | Recommended: Pattern matching with confidence scoring + manual review |
| **No-rubric grading** | System behavior when rubric omitted | Recommended: Relevance-only marks with LOW confidence warning |
| **Similarity thresholds** | What constitutes "high similarity"? | Recommended: 30% exact, 70% lexical, 85% semantic (validate on test dataset) |
| **AI detector** | Which provider/method? | Recommended: Defer to Phase 4, do NOT include in MVP, requires ethical review |
| **OCR engine** | Tesseract vs. cloud API? | Recommended: Tesseract for Phase 4, evaluate cloud if accuracy insufficient |
| **Hosting** | Which providers? | Recommended: Railway/Render + Neon + Cloudflare R2 + Vercel for MVP |
| **Data retention** | How long to keep evaluations? | Recommended: 30-day default, configurable, honor delete requests immediately |

### Open Questions Requiring Your Decision

**None blocking Phase 0-1 implementation.** All critical decisions have recommended defaults. Optional decisions (AI detector provider, OCR accuracy threshold, enterprise hosting) deferred to Phase 4-5 with clear evaluation criteria.

---

## 4. Next Implementation Milestone

### **Phase 0.2: Database Schema Implementation**

**Goal:** Runnable database with all tables, constraints, and migrations.

**Duration:** 3-4 days

**Tasks:**

1. **Initialize Alembic** (Database migration tool)
   ```bash
   cd backend
   alembic init alembic
   alembic revision -m "0001_create_tenants_users"
   ```

2. **Create Migrations in Order:**
   - `0001_create_tenants_users.py` → tenants, users tables
   - `0002_create_evaluations_questions_rubric.py` → evaluations, questions, rubric_criteria
   - `0003_create_submissions_chunks.py` → submissions, submission_chunks
   - `0004_create_relevance_comparisons.py` → relevance_results, **comparisons** (with canonical pair constraint), matched_passages
   - `0005_create_grading_audit.py` → grading_results, audit_logs, processing_jobs

3. **Critical Constraints to Implement:**
   ```sql
   -- Canonical pair storage (CRITICAL)
   ALTER TABLE comparisons 
     ADD CONSTRAINT check_canonical_pair 
     CHECK (submission_a_id < submission_b_id);
   
   CREATE UNIQUE INDEX idx_comparisons_canonical_pair 
     ON comparisons(evaluation_id, submission_a_id, submission_b_id);
   
   -- Other uniqueness constraints
   CREATE UNIQUE INDEX idx_relevance_unique 
     ON relevance_results(submission_id, question_id);
   
   CREATE UNIQUE INDEX idx_submissions_hash 
     ON submissions(evaluation_id, file_hash);
   ```

4. **Create SQLAlchemy Models** matching schema in `backend/app/models/`:
   - `tenant.py`, `user.py`
   - `evaluation.py`, `question.py`, `rubric_criteria.py`
   - `submission.py`, `submission_chunk.py`
   - `relevance_result.py`, `comparison.py`, `matched_passage.py`
   - `grading_result.py`, `audit_log.py`, `processing_job.py`

5. **Write Database Seed Script** (`backend/scripts/seed_db.py`):
   - Create 2 test tenants
   - Create 5 test users (3 teachers, 2 admins)
   - Create 2 test evaluations with questions and rubric
   - Create 10 test submissions
   - Useful for frontend development and testing

**Acceptance Criteria:**
- [ ] `alembic upgrade head` runs without errors
- [ ] All 14 tables created with correct columns, types, constraints
- [ ] Foreign keys cascade correctly
- [ ] Unique constraints prevent duplicate canonical pairs
- [ ] Seed script populates test data
- [ ] Can query data with SQLAlchemy models

**Commands to Run:**
```bash
# Start PostgreSQL with Docker Compose
docker-compose up -d postgres

# Run migrations
cd backend
alembic upgrade head

# Verify tables created
psql -U plagix_user -d plagix_db -c "\dt"

# Seed test data
python scripts/seed_db.py

# Verify data
psql -U plagix_user -d plagix_db -c "SELECT * FROM tenants;"
```

**Next After 0.2:**
- Phase 0.3: Docker Compose environment (API, workers, Redis)
- Phase 0.4: Authentication scaffold (register, login, JWT)
- Phase 0.5: CI/CD skeleton (GitHub Actions)

---

## 5. Proposed Git Commits

### Commits Already Made:
```
dfe25e4 docs: Add processing pipeline, technology stack ADR, phase plan, and open questions
4111284 docs: Add foundational planning documents - README, requirements traceability, system overview, and data model
89d69c2 docs: add PLAGIX project brief and SRS
```

### Next Commit (After Completing This Summary):
```
git add docs/PLANNING_SUMMARY.md
git commit -m "docs: Add planning session summary with next milestone"
git push origin main
```

### Future Implementation Commits (Phase 0.2):
```
git commit -m "chore: Initialize Alembic for database migrations"
git commit -m "feat(db): Add tenants and users tables with constraints"
git commit -m "feat(db): Add evaluations, questions, and rubric tables"
git commit -m "feat(db): Add submissions and text extraction tables"
git commit -m "feat(db): Add comparisons with canonical pair constraint"
git commit -m "feat(db): Add grading, audit, and job tracking tables"
git commit -m "feat(db): Add SQLAlchemy models for all entities"
git commit -m "chore: Add database seed script with test data"
git commit -m "docs: Update README with database setup instructions"
```

**Commit Strategy:** Small, focused commits (one logical change each) with clear conventional commit messages. Push after each completed task to maintain progress visibility.

---

## 6. Key Success Metrics (MVP)

From Phase Plan, success defined as:

**Phase 3 Exit (MVP Complete):**
- [ ] 10 teachers successfully use PLAGIX for real evaluations
- [ ] Average processing time: <5 minutes for 50 submissions
- [ ] False-positive rate: <10% on test dataset
- [ ] Zero tenant isolation violations
- [ ] Teacher satisfaction: 4/5 or higher

**Technical Milestones:**
- [ ] Database schema complete with all constraints (Phase 0.2)
- [ ] Authentication working (Phase 0.4)
- [ ] File upload and extraction working (Phase 1)
- [ ] Relevance analysis working (Phase 2)
- [ ] Exactly N×(N-1)/2 comparisons generated (Phase 2)
- [ ] Teacher review and approval working (Phase 3)
- [ ] Reports exportable (Phase 3)

---

## 7. Risk Reminders

| Risk | Mitigation Strategy |
|------|---------------------|
| **NLP model inference too slow** | Benchmark in Phase 2 with 100 submissions; add GPU or lighter model if needed |
| **ZIP bomb bypass** | Multiple safety checks (ratio, timeout, size); tested in Phase 1 |
| **False positives in similarity** | Validate on labeled test dataset; tune thresholds; require teacher review |
| **Canonical pair constraint violation** | Database-enforced uniqueness; idempotent task design; integration tests |
| **Scope creep (LMS features)** | Refer to SRS; standalone evaluation utility only; defer course management |

---

## 8. Final Checklist

**Planning Phase (Phase 0.1):**
- [x] SRS read and extracted to text format
- [x] README created with product summary, stack, status
- [x] Requirements traceability matrix complete
- [x] System overview with Mermaid diagrams complete
- [x] Data model with ERD and canonical pair storage complete
- [x] Processing pipeline detailed with failure handling complete
- [x] ADR-0001 technology stack rationale complete
- [x] Phase plan with testable milestones complete
- [x] Open questions documented with recommendations
- [x] Planning summary created (this document)
- [x] All documents committed to Git (2 commits)
- [ ] Planning summary committed to Git (next commit)

**Ready to Start:**
- [x] Architecture validated against SRS requirements
- [x] All critical decisions made or deferred with rationale
- [x] Database schema designed with constraints
- [x] Implementation path clear (Phase 0.2 → 0.3 → 0.4 → 0.5 → Phase 1)
- [x] No blocking ambiguities remain
- [ ] Begin Phase 0.2: Database Schema Implementation

---

## Commands to Execute Next

```bash
# Commit this summary
git add docs/PLANNING_SUMMARY.md
git commit -m "docs: Add planning session summary with next milestone"
git push origin main

# Start Phase 0.2: Database Schema Implementation
mkdir -p backend/app/models backend/app/core backend/scripts
cd backend
pip install alembic sqlalchemy psycopg2-binary python-dotenv
alembic init alembic

# Follow Phase 0.2 tasks above...
```

---

**PLANNING PHASE COMPLETE. NO IMPLEMENTATION CODE WRITTEN YET.**

All architectural decisions documented. Database schema designed with critical constraints (canonical pair storage, tenant isolation). Pipeline stages detailed with failure handling. Ready for Phase 0.2 implementation.
