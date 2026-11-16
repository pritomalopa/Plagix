# Phase Plan and Roadmap

**PLAGIX v1.0**  
**Status:** Planning phase  
**Last updated:** 16 November 2026

---

## Purpose

This document breaks down the PLAGIX implementation into testable phases and milestones, from foundation setup through production-ready SaaS deployment.

---

## Phasing Strategy

Each phase:
- Builds on previous phases
- Has clear exit criteria and acceptance tests
- Delivers incremental value
- Can be demonstrated to stakeholders
- Includes testing and documentation

**Philosophy:** Small, testable milestones over big-bang releases.

---

## Phase 0: Foundation (Week 1-2)

**Goal:** Establish documented, runnable development baseline.

### Milestones

| ID | Milestone | Deliverables | Acceptance Criteria |
|----|-----------|--------------|---------------------|
| **0.1** | Project structure | Repository, README, planning docs | All planning documents reviewed and committed |
| **0.2** | Database schema | Alembic migrations, SQLAlchemy models | `alembic upgrade head` creates all tables with constraints |
| **0.3** | Docker environment | docker-compose.yml, Dockerfile | `docker-compose up` starts API, DB, Redis, workers |
| **0.4** | Authentication scaffold | User registration, login, JWT/session | User can register, login, receive auth token |
| **0.5** | CI/CD skeleton | GitHub Actions workflows | Linters and type checkers run on every PR |

### Tasks

#### 0.1 Project Structure
- [x] Create repository with proper .gitignore
- [x] Write README with product summary and stack
- [x] Create docs/requirements/requirements-traceability.md
- [x] Create docs/architecture/system-overview.md with Mermaid diagrams
- [x] Create docs/architecture/data-model.md
- [x] Create docs/architecture/processing-pipeline.md
- [x] Create docs/decisions/ADR-0001-technology-stack.md
- [ ] Create docs/roadmap/phase-plan.md (this document)
- [ ] Create docs/open-questions.md

#### 0.2 Database Schema
- [ ] Initialize Alembic in backend/
- [ ] Create migration: `0001_create_tenants_users.py`
- [ ] Create migration: `0002_create_evaluations_questions_rubric.py`
- [ ] Create migration: `0003_create_submissions_chunks.py`
- [ ] Create migration: `0004_create_relevance_comparisons.py`
- [ ] Create migration: `0005_create_grading_audit.py`
- [ ] Create SQLAlchemy models matching schema
- [ ] Write database seed script for test data
- [ ] Verify all foreign keys, unique constraints, indexes

#### 0.3 Docker Environment
- [ ] Create backend/Dockerfile (Python 3.11, FastAPI)
- [ ] Create frontend/Dockerfile (Node.js 18, Next.js)
- [ ] Create docker-compose.yml (API, frontend, PostgreSQL, Redis, worker)
- [ ] Create .env.example with required environment variables
- [ ] Document local setup in README
- [ ] Test: `docker-compose up` → all services healthy

#### 0.4 Authentication Scaffold
- [ ] Implement user registration endpoint (POST /auth/register)
- [ ] Implement login endpoint (POST /auth/login)
- [ ] Implement JWT or session-based authentication
- [ ] Create auth middleware for protected routes
- [ ] Implement tenant creation on first user registration
- [ ] Write unit tests for auth flows
- [ ] Test: User can register, login, access protected endpoint

#### 0.5 CI/CD Skeleton
- [ ] Create .github/workflows/backend-lint.yml (Ruff)
- [ ] Create .github/workflows/backend-typecheck.yml (mypy)
- [ ] Create .github/workflows/backend-test.yml (pytest)
- [ ] Create .github/workflows/frontend-lint.yml (ESLint)
- [ ] Create .github/workflows/frontend-typecheck.yml (tsc)
- [ ] Create .github/workflows/frontend-test.yml (Jest)
- [ ] Configure status checks for pull requests

### Exit Criteria
- [ ] All planning documents committed and reviewed
- [ ] `docker-compose up` starts full development stack
- [ ] Database migrations run successfully
- [ ] User can register and authenticate
- [ ] CI passes on sample code
- [ ] Documentation is accurate and complete

**Estimated Duration:** 1-2 weeks

---

## Phase 1: MVP Ingestion (Week 3-4)

**Goal:** Teacher can create evaluation and reliably see extracted submissions.

### Milestones

| ID | Milestone | Deliverables | Acceptance Criteria |
|----|-----------|--------------|---------------------|
| **1.1** | Evaluation CRUD | API endpoints, frontend forms | Teacher can create/read/update/delete evaluation |
| **1.2** | File upload API | Multipart upload, object storage | Files uploaded to S3-compatible storage |
| **1.3** | Ingestion worker | ZIP extraction, validation | ZIP safely extracted, submissions created |
| **1.4** | Document worker | Text extraction (PDF/DOCX/TXT) | Text extracted with page/offset preservation |
| **1.5** | Progress tracking | Job status API, frontend polling | Teacher sees extraction progress in real-time |

### Tasks

#### 1.1 Evaluation CRUD
- [ ] Create Evaluation model and schema
- [ ] Implement POST /evaluations (create)
- [ ] Implement GET /evaluations (list with tenant filter)
- [ ] Implement GET /evaluations/{id} (detail)
- [ ] Implement PATCH /evaluations/{id} (update)
- [ ] Implement DELETE /evaluations/{id} (soft delete or cascade)
- [ ] Add tenant authorization checks
- [ ] Create Next.js evaluation creation form
- [ ] Create evaluations dashboard page
- [ ] Write integration tests

#### 1.2 File Upload API
- [ ] Configure object storage (MinIO locally, R2 candidate for production)
- [ ] Implement POST /evaluations/{id}/upload (multipart)
- [ ] Validate file count, size, MIME type
- [ ] Store files with tenant-scoped keys
- [ ] Return upload status with file IDs
- [ ] Create Next.js upload UI with drag-drop
- [ ] Handle upload errors gracefully
- [ ] Write integration tests (AC-02)

#### 1.3 Ingestion Worker
- [ ] Create Celery app configuration
- [ ] Implement `ingestion_task.py`
- [ ] Implement safe ZIP extraction with security checks
- [ ] Implement path traversal prevention (AC-03)
- [ ] Implement ZIP bomb detection (AC-03)
- [ ] Calculate SHA-256 file hashes
- [ ] Detect duplicates (AC-08)
- [ ] Derive student labels from filenames
- [ ] Create submission records
- [ ] Write unit tests for ZIP safety
- [ ] Write integration tests (AC-01, AC-03)

#### 1.4 Document Worker
- [ ] Implement `document_task.py`
- [ ] Implement PDF extraction (PyMuPDF)
- [ ] Implement DOCX extraction (python-docx)
- [ ] Implement TXT extraction
- [ ] Preserve page/paragraph/offset for evidence tracing
- [ ] Store original and normalized text separately
- [ ] Detect scanned PDFs
- [ ] Handle corrupt/malformed files gracefully
- [ ] Write unit tests for extraction
- [ ] Write integration tests (AC-08)

#### 1.5 Progress Tracking
- [ ] Create ProcessingJob model
- [ ] Implement job status updates in workers
- [ ] Implement GET /evaluations/{id}/status
- [ ] Implement GET /evaluations/{id}/submissions
- [ ] Create progress indicator component in frontend
- [ ] Implement real-time polling (or WebSocket in later phase)
- [ ] Display per-file extraction status
- [ ] Write integration tests

### Functional Requirements Covered
- FR-01: Evaluation creation
- FR-02: Question context
- FR-03: No course dependency
- FR-04: ZIP upload
- FR-05: Individual upload
- FR-06: File validation
- FR-07: Student mapping
- FR-08: Duplicate detection
- FR-09: Text extraction
- FR-11: Processing queue
- FR-28: Multi-tenant isolation

### Exit Criteria
- [ ] Teacher can create evaluation with question and rubric
- [ ] Teacher can upload ZIP and individual files
- [ ] System safely extracts ZIP with security checks (AC-03)
- [ ] System extracts text from PDF/DOCX/TXT (AC-01)
- [ ] Teacher sees extraction progress and per-file status
- [ ] All Phase 1 integration tests pass
- [ ] No secrets in Git, proper tenant isolation verified

**Estimated Duration:** 2 weeks

---

## Phase 2: Relevance + Text Similarity (Week 5-7)

**Goal:** Complete explainable text-analysis report for a batch.

### Milestones

| ID | Milestone | Deliverables | Acceptance Criteria |
|----|-----------|--------------|---------------------|
| **2.1** | Relevance worker | Question alignment analysis | Each submission has relevance category + evidence |
| **2.2** | Comparison worker | Pairwise similarity engine | Exactly N×(N-1)/2 comparisons created (AC-04) |
| **2.3** | Similarity algorithms | Exact, lexical, semantic | Multiple dimensions calculated and stored |
| **2.4** | Matched passages | Evidence extraction | Matched text traced to page/offset (AC-08) |
| **2.5** | Review dashboard | Submission list, comparison view | Teacher can view results and evidence |

### Tasks

#### 2.1 Relevance Worker
- [ ] Implement `relevance_task.py`
- [ ] Integrate sentence-transformers (multilingual model)
- [ ] Calculate semantic similarity (question vs. answer)
- [ ] Incorporate reference answer if provided
- [ ] Generate relevance category and confidence
- [ ] Extract supporting evidence excerpts
- [ ] Store rationale and model version
- [ ] Handle Bangla and English text
- [ ] Write unit tests
- [ ] Write integration tests (AC-07)

#### 2.2 Comparison Worker
- [ ] Implement `comparison_task.py`
- [ ] Implement canonical pair ID logic
- [ ] Generate N×(N-1)/2 comparison jobs
- [ ] Enforce uniqueness constraint on (eval_id, sub_a_id, sub_b_id)
- [ ] Ensure A-B and B-A resolve to same result (AC-05)
- [ ] Implement idempotent retry (AC-06)
- [ ] Verify no self-comparisons
- [ ] Write unit tests
- [ ] Write integration tests (AC-04, AC-05, AC-06)

#### 2.3 Similarity Algorithms
- [ ] Implement exact similarity (Winnowing fingerprints)
- [ ] Implement lexical similarity (TF-IDF + cosine)
- [ ] Implement semantic similarity (sentence embeddings)
- [ ] Store separate scores for each dimension (AC-16)
- [ ] Implement common-content filtering (AC-09)
- [ ] Filter question text from comparisons
- [ ] Write unit tests with test dataset
- [ ] Benchmark performance on 100 submissions

#### 2.4 Matched Passages
- [ ] Implement passage extraction in comparison worker
- [ ] Locate matched text in both submissions
- [ ] Store page/offset for both sides
- [ ] Store match type (exact, lexical, semantic)
- [ ] Ensure traceability to original text (AC-08)
- [ ] Write unit tests

#### 2.5 Review Dashboard
- [ ] Create GET /submissions/{id}/relevance endpoint
- [ ] Create GET /submissions/{id}/comparisons endpoint
- [ ] Create GET /comparisons/{id}/passages endpoint
- [ ] Create submission list page with filters
- [ ] Create submission detail page with evidence
- [ ] Create side-by-side comparison view with highlighting
- [ ] Display relevance category, score, evidence
- [ ] Display top similarity matches with passages
- [ ] Write E2E tests

### Functional Requirements Covered
- FR-12: Relevance analysis
- FR-13: Relevance evidence
- FR-14: Batch pairwise comparison
- FR-15: Unique pair storage
- FR-16: Similarity dimensions
- FR-17: Matched passage evidence
- FR-18: Common-content handling

### Test Dataset (Phase 2 Validation)
- [ ] Create exact-copy pair
- [ ] Create near-copy pair
- [ ] Create paraphrase pair
- [ ] Create common-prompt pair
- [ ] Create unrelated pair
- [ ] Create short-answer pair
- [ ] Create Bangla/English pair
- [ ] Measure precision, recall, false-positive rate

### Exit Criteria
- [ ] Relevance analysis completes before comparison (AC-07)
- [ ] Exactly N×(N-1)/2 comparisons created (AC-04)
- [ ] A-B and B-A return same stored result (AC-05)
- [ ] Retry does not duplicate comparisons (AC-06)
- [ ] Matched passages traced to source page/offset (AC-08)
- [ ] Common question text excluded from evidence (AC-09)
- [ ] Test dataset validation passes (precision/recall documented)
- [ ] Teacher can view complete analysis report

**Estimated Duration:** 3 weeks

---

## Phase 3: Grading + Reports (Week 8-9)

**Goal:** Teacher can approve and export defensible results.

### Milestones

| ID | Milestone | Deliverables | Acceptance Criteria |
|----|-----------|--------------|---------------------|
| **3.1** | Grading worker | Provisional marks calculation | Rubric-based marks with evidence |
| **3.2** | Teacher override | Mark editing, flag dismissal | Teacher can edit marks and record reason (AC-10) |
| **3.3** | Audit logging | Immutable audit trail | Grade changes recorded (AC-10) |
| **3.4** | Report generation | PDF and CSV exports | Batch summary and individual reports (AC-13) |
| **3.5** | Data deletion | Evaluation deletion workflow | Files and results deleted per policy (AC-14) |

### Tasks

#### 3.1 Grading Worker
- [ ] Implement `grading_task.py`
- [ ] Calculate provisional marks from relevance + rubric
- [ ] Generate criterion-by-criterion scores
- [ ] Keep similarity signals separate (not auto-deducted)
- [ ] Apply configurable review thresholds
- [ ] Store suggested marks and confidence
- [ ] Handle no-rubric case with warning
- [ ] Write unit tests

#### 3.2 Teacher Override
- [ ] Implement PATCH /submissions/{id}/grade
- [ ] Allow mark editing with reason
- [ ] Allow flag dismissal
- [ ] Update grading status to 'approved'
- [ ] Create mark override UI in frontend
- [ ] Show original suggested vs. final marks
- [ ] Write integration tests (AC-10)

#### 3.3 Audit Logging
- [ ] Create AuditLog model
- [ ] Implement audit middleware
- [ ] Log evaluation creation, upload, grade changes, deletion
- [ ] Store actor, timestamp, changes (before/after)
- [ ] Implement GET /audit-logs (admin only)
- [ ] Write unit tests
- [ ] Verify immutability (AC-10)

#### 3.4 Report Generation
- [ ] Implement `report_task.py`
- [ ] Generate batch summary PDF
- [ ] Generate individual submission PDF
- [ ] Generate CSV export (student, marks, status)
- [ ] Include relevance evidence, matched passages
- [ ] Include similarity flags as separate section
- [ ] Add plagiarism disclaimer text
- [ ] Store reports in object storage
- [ ] Implement POST /evaluations/{id}/reports
- [ ] Implement report download UI
- [ ] Write integration tests (AC-13)

#### 3.5 Data Deletion
- [ ] Implement DELETE /evaluations/{id} with cascade
- [ ] Delete submission files from object storage
- [ ] Delete generated reports
- [ ] Preserve minimal audit tombstone
- [ ] Implement deletion confirmation UI
- [ ] Write integration tests (AC-14)

### Functional Requirements Covered
- FR-22: Grading policy
- FR-23: Teacher override
- FR-24: Reports
- FR-25: Audit log
- FR-26: Delete data
- FR-27: Progress and retry

### Exit Criteria
- [ ] Grading generates provisional marks based on rubric
- [ ] Similarity shown as separate integrity signal (AC-11)
- [ ] Teacher can override marks and record reason (AC-10)
- [ ] Audit log captures grade changes (AC-10)
- [ ] Reports exported with correct values (AC-13)
- [ ] Deletion removes files per policy (AC-14)
- [ ] No automatic accusations from similarity alone (AC-11)

**Estimated Duration:** 2 weeks

---

## Phase 4: Advanced Analysis (Week 10-12)

**Goal:** Advanced modules pass evaluation on labeled test datasets.

### Milestones

| ID | Milestone | Deliverables | Acceptance Criteria |
|----|-----------|--------------|---------------------|
| **4.1** | Semantic embeddings | pgvector integration | Semantic retrieval accelerated with vector search |
| **4.2** | MinHash/LSH optimization | Candidate retrieval | Large batches (1000+ submissions) processed efficiently |
| **4.3** | OCR processing | Scanned PDF support | Text extracted from scanned documents with confidence |
| **4.4** | Citation handling | Reference section parsing | Cited content shown separately |
| **4.5** | Code similarity | Language-aware comparison | Python/C++ code compared with token/AST analysis |
| **4.6** | AI-writing signal | Experimental detector | Cautious signal with limitations and false-positive rate |

### Tasks

#### 4.1 Semantic Embeddings + pgvector
- [ ] Enable pgvector extension in PostgreSQL
- [ ] Add embedding_ref column to submission_chunks
- [ ] Store sentence embeddings during relevance analysis
- [ ] Create vector similarity index
- [ ] Implement semantic retrieval for top-k candidates
- [ ] Benchmark performance improvement
- [ ] Write integration tests

#### 4.2 MinHash/LSH Optimization
- [ ] Implement MinHash signature generation
- [ ] Implement LSH candidate retrieval
- [ ] Use LSH to filter comparison pairs (top 10% candidates)
- [ ] Run full comparison only on candidates
- [ ] Benchmark on 1000-submission dataset
- [ ] Document trade-offs (recall vs. speed)

#### 4.3 OCR Processing
- [ ] Integrate Tesseract or cloud OCR API
- [ ] Detect scanned PDFs in document worker
- [ ] Trigger OCR for low selectable text
- [ ] Store confidence scores per page
- [ ] Mark low-confidence extractions for review
- [ ] Test on scanned PDF dataset
- [ ] Document accuracy and limitations

#### 4.4 Citation Handling
- [ ] Implement reference section detection (regex patterns)
- [ ] Parse common citation formats (APA, MLA, IEEE)
- [ ] Tag cited passages in comparison
- [ ] Show cited content separately in UI
- [ ] Write unit tests with academic paper samples

#### 4.5 Code Similarity
- [ ] Implement code file detection (.py, .cpp, .java, .js)
- [ ] Implement language-aware tokenization (Python, C++, Java)
- [ ] Implement identifier normalization (rename variables)
- [ ] Implement token n-gram comparison
- [ ] Optionally parse AST (tree-sitter or language-specific parsers)
- [ ] Compare AST subtrees for structural similarity
- [ ] Show matched code spans with line numbers
- [ ] Test on code plagiarism dataset
- [ ] Document common starter code handling

#### 4.6 AI-Writing Signal (Experimental)
- [ ] Research open-source AI detectors (GPTZero alternatives)
- [ ] Integrate detector with explicit teacher opt-in
- [ ] Store model/version metadata
- [ ] Calculate false-positive rate on student writing samples
- [ ] Show result with confidence and limitations
- [ ] Add prominent disclaimer in UI
- [ ] Document that this is NOT proof of AI authorship
- [ ] Write ethical guidelines document

### Functional Requirements Covered
- FR-10: OCR
- FR-19: Citation/reference handling
- FR-20: Code analysis
- FR-21: AI-writing signal

### Exit Criteria
- [ ] Semantic retrieval accelerates large-batch comparisons
- [ ] OCR extracts scanned PDFs with confidence tracking
- [ ] Citations shown separately from plagiarism evidence
- [ ] Code similarity works for Python and C++
- [ ] AI-writing detector false-positive rate documented
- [ ] All advanced modules validated on test datasets
- [ ] Limitations clearly communicated to teachers

**Estimated Duration:** 3 weeks

---

## Phase 5: SaaS Hardening (Week 13-16)

**Goal:** Secure, supportable SaaS release.

### Milestones

| ID | Milestone | Deliverables | Acceptance Criteria |
|----|-----------|--------------|---------------------|
| **5.1** | Security testing | Penetration tests, OWASP checks | All high/critical vulnerabilities resolved |
| **5.2** | Tenant isolation hardening | Row-level security, admin access controls | Verified cross-tenant access impossible (AC-12) |
| **5.3** | Usage limits and billing | Per-tenant quotas, usage tracking | Usage tracked, limits enforced |
| **5.4** | Monitoring and alerting | Logs, metrics, dashboards | Operational visibility and alerting |
| **5.5** | Backups and disaster recovery | Automated backups, restore procedures | Database and storage backed up daily |
| **5.6** | Production deployment | Staging and production environments | PLAGIX deployed and accessible |

### Tasks

#### 5.1 Security Testing
- [ ] Run OWASP ZAP or similar scanner
- [ ] Test SQL injection, XSS, CSRF protections
- [ ] Test file upload attacks (path traversal, ZIP bombs)
- [ ] Test authentication bypass attempts
- [ ] Test tenant isolation violations (AC-12)
- [ ] Run dependency vulnerability scan (Snyk, Safety)
- [ ] Conduct code review for secrets, sensitive data exposure
- [ ] Document and fix all high/critical issues

#### 5.2 Tenant Isolation Hardening
- [ ] Implement row-level security policies in PostgreSQL
- [ ] Verify tenant_id filtering on all queries
- [ ] Test cross-tenant API access attempts
- [ ] Implement admin role with elevated auth
- [ ] Audit all object storage key generation
- [ ] Write tenant isolation test suite (AC-12)

#### 5.3 Usage Limits and Billing
- [ ] Define per-tenant quotas (evaluations, submissions, storage)
- [ ] Implement usage tracking middleware
- [ ] Implement quota enforcement in API
- [ ] Create usage dashboard for admins
- [ ] Design subscription plans (free, pro, enterprise)
- [ ] Integrate payment provider (Stripe candidate)
- [ ] Implement subscription lifecycle

#### 5.4 Monitoring and Alerting
- [ ] Set up structured logging (JSON logs)
- [ ] Integrate log aggregation (Loki, CloudWatch, Datadog)
- [ ] Define key metrics (API latency, worker queue depth, error rates)
- [ ] Set up metrics collection (Prometheus, CloudWatch)
- [ ] Create operational dashboards (Grafana)
- [ ] Configure alerts (high error rate, queue backlog, database issues)
- [ ] Document on-call procedures

#### 5.5 Backups and Disaster Recovery
- [ ] Configure automated PostgreSQL backups (daily)
- [ ] Configure object storage versioning/replication
- [ ] Test database restore procedure
- [ ] Document recovery time objectives (RTO)
- [ ] Document recovery point objectives (RPO)
- [ ] Create disaster recovery runbook

#### 5.6 Production Deployment
- [ ] Select hosting providers (API, database, storage, workers)
- [ ] Set up staging environment (isolated from production)
- [ ] Set up production environment
- [ ] Configure secrets management (AWS Secrets Manager, Vault)
- [ ] Configure CDN for frontend (Cloudflare)
- [ ] Set up SSL certificates
- [ ] Configure DNS
- [ ] Deploy backend API
- [ ] Deploy frontend
- [ ] Deploy workers
- [ ] Run smoke tests
- [ ] Create deployment runbook

### Non-Functional Requirements Validation
- NFR-01: Performance (baseline: 100 submissions, 4,950 pairs)
- NFR-02: Scalability (horizontal worker scaling)
- NFR-03: Reliability (idempotent tasks, retry logic)
- NFR-04: Usability (user testing)
- NFR-05: Explainability (evidence tracing)
- NFR-06: Accessibility (automated axe-core tests)
- NFR-07: Maintainability (code review)
- NFR-08: Observability (logging, metrics)
- NFR-09: Portability (multi-provider deployment)
- NFR-10: Cost control (usage tracking)

### Exit Criteria
- [ ] All high/critical security issues resolved
- [ ] Tenant isolation verified (AC-12)
- [ ] Usage limits enforced
- [ ] Monitoring and alerting operational
- [ ] Backups automated and tested
- [ ] Production environment deployed
- [ ] Privacy policy and terms of service published
- [ ] Incident response process documented
- [ ] System ready for beta users

**Estimated Duration:** 4 weeks

---

## Post-MVP Roadmap

### Phase 6: Student Portal (Future)
- Student account registration
- Self-submission upload
- View feedback and marks
- Appeal workflow

### Phase 7: Historical Comparison (Future)
- Cross-batch comparison (with consent)
- Teacher-managed reference corpus
- Institutional knowledge base

### Phase 8: Integrations (Future)
- LMS integration (Google Classroom, Moodle, Canvas)
- Single sign-on (Google, Microsoft, SAML)
- Plagiarism database APIs (optional)

---

## Testing Strategy

### Unit Tests
- Core logic: canonical pair generation, text normalization, similarity algorithms
- Database models: constraints, relationships
- Workers: task logic, retry behavior
- Coverage target: 80%+

### Integration Tests
- API endpoints with database
- Worker tasks with database and storage
- End-to-end workflows (upload → extraction → analysis → grading)
- Acceptance criteria validation (AC-01 through AC-14)

### E2E Tests
- Frontend user workflows
- Real file uploads and processing
- Teacher review and approval
- Report generation and download

### Performance Tests
- 100-submission baseline (4,950 pairs)
- 500-submission stress test
- Concurrent evaluation processing
- Worker queue saturation

### Security Tests
- OWASP Top 10 checks
- File upload attacks
- Tenant isolation violations
- Authentication bypass attempts

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| NLP model inference too slow | Medium | High | Benchmark early; optimize or add GPU workers |
| ZIP bomb bypass detection | Low | High | Use multiple safety checks; timeout extraction |
| Database performance bottleneck | Medium | Medium | Add indexes, connection pooling; monitor query performance |
| Object storage costs exceed budget | Low | Medium | Implement lifecycle policies; compress reports |
| False positives in similarity detection | High | High | Use test dataset; tune thresholds; require teacher review |
| AI detector inaccurate | High | High | Make experimental; show limitations; never auto-accuse |
| Scope creep into LMS features | Medium | Medium | Refer to SRS; defer out-of-scope features |

---

## Success Metrics

### MVP Success (Phase 3 complete)
- [ ] 10 teachers successfully use PLAGIX for real evaluations
- [ ] Average processing time: <5 minutes for 50 submissions
- [ ] False-positive rate: <10% on test dataset
- [ ] Zero tenant isolation violations
- [ ] Teacher satisfaction: 4/5 or higher

### Production Success (Phase 5 complete)
- [ ] 100+ evaluations processed
- [ ] System uptime: 99.5%+
- [ ] Average API response time: <200ms
- [ ] Zero data breaches
- [ ] Teacher retention: 70%+ after first month

---

## Dependencies and Blockers

### External Dependencies
- Hosting provider selection (cost, region, data protection)
- PyMuPDF license compliance for SaaS (AGPL)
- Multilingual model accuracy for Bangla (validation needed)
- OCR engine selection (accuracy vs. cost)
- AI-writing detector availability (ethical/legal review)

### Internal Dependencies
- Database schema finalized (Phase 0.2) → blocks all data operations
- Authentication working (Phase 0.4) → blocks tenant isolation
- Object storage configured (Phase 1.2) → blocks file uploads
- Relevance analysis complete (Phase 2.1) → blocks comparison (per SRS)

---

## Next Steps (Immediate)

### Week 1 (Phase 0 Completion)
1. Finalize planning documents (this document, open-questions.md)
2. Initialize Alembic and create database migrations
3. Set up Docker Compose environment
4. Implement authentication scaffold
5. Configure GitHub Actions CI

### Week 2 (Phase 0 → Phase 1 Transition)
1. Complete Phase 0 exit criteria validation
2. Kick off Phase 1.1 (Evaluation CRUD)
3. Set up object storage (MinIO locally)
4. Begin frontend scaffolding (Next.js pages)

---

## Communication Plan

### Weekly Demo
- Show working features to stakeholders
- Gather feedback on UX and priorities
- Adjust backlog as needed

### Phase Review
- At each phase completion, conduct review meeting
- Validate exit criteria met
- Decide go/no-go for next phase

### Documentation Updates
- Keep README current with implementation status
- Update architecture docs as design evolves
- Record decisions in ADR format

---

## References

- [PLAGIX SRS v1.0](../PLAGIX_SRS_v1.0.pdf) - Requirements source of truth
- [Requirements Traceability](../requirements/requirements-traceability.md) - FR mapping
- [System Overview](../architecture/system-overview.md) - Architecture
- [Data Model](../architecture/data-model.md) - Database schema
- [Processing Pipeline](../architecture/processing-pipeline.md) - Worker logic
- [ADR-0001: Technology Stack](../decisions/ADR-0001-technology-stack.md) - Stack rationale

---

**Status:** Planning complete. Ready for Phase 0.2 (Database Schema) implementation.
