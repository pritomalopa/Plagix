# Requirements Traceability Matrix

**PLAGIX v1.0**  
**Status:** Planning phase  
**Last updated:** 16 November 2026

---

## Purpose

This document maps every functional requirement from the SRS to planned implementation modules, dependencies, and acceptance test references. It serves as a bridge between requirements and implementation.

---

## Functional Requirements Traceability

| ID | Requirement | Priority | Planned Module | Dependencies | Acceptance Test | Notes |
|----|-------------|----------|----------------|--------------|-----------------|-------|
| **FR-01** | Evaluation creation | MUST | `backend/app/api/evaluations.py` | Authentication, database | AC-01 | Teacher can create evaluation with title, question, language, max marks |
| **FR-02** | Question context | MUST | `backend/app/models/questions.py`, `backend/app/models/rubric_criteria.py` | FR-01 | Phase 1 test suite | Support sub-questions, rubric, reference answer, expected concepts |
| **FR-03** | No course dependency | MUST | Application architecture | FR-01 | AC-01, manual verification | Evaluation creation workflow independent of course/class |
| **FR-04** | ZIP upload | MUST | `backend/app/services/ingestion.py`, `backend/app/workers/extraction_worker.py` | FR-01, object storage | AC-01, AC-03 | Safe extraction with validation |
| **FR-05** | Individual upload | MUST | `backend/app/api/uploads.py` | FR-01, object storage | AC-02 | Mix ZIP and individual files in same job |
| **FR-06** | File validation | MUST | `backend/app/services/file_validator.py` | FR-04, FR-05 | AC-03 | MIME, signature, size, archive safety checks |
| **FR-07** | Student mapping | MUST | `backend/app/services/student_mapper.py` | FR-04, FR-05 | Phase 1 test suite | Derive labels from filenames, allow CSV mapping |
| **FR-08** | Duplicate detection | MUST | `backend/app/services/deduplication.py` | FR-06 | Phase 1 test suite | Hash-based duplicate identification |
| **FR-09** | Text extraction | MUST | `backend/app/workers/document_worker.py` | FR-06 | AC-08 | PDF/DOCX/TXT with page/offset preservation |
| **FR-10** | OCR | SHOULD | `backend/app/services/ocr_service.py` | FR-09 | Phase 4 test suite | Scanned PDF processing with confidence tracking |
| **FR-11** | Processing queue | MUST | Redis + Celery workers | FR-04, FR-05 | AC-06 | Async background jobs with state management |
| **FR-12** | Relevance analysis | MUST | `backend/app/services/relevance_analyzer.py` | FR-09 | AC-07 | Evaluate answer alignment before similarity |
| **FR-13** | Relevance evidence | MUST | `backend/app/models/relevance_results.py` | FR-12 | AC-07 | Category, score, explanation, excerpts |
| **FR-14** | Batch pairwise comparison | MUST | `backend/app/services/comparison_engine.py` | FR-09, FR-12 | AC-04 | N×(N-1)/2 unique pairs, no self-comparison |
| **FR-15** | Unique pair storage | MUST | `backend/app/models/comparisons.py` | FR-14 | AC-04, AC-05 | Canonical ordering: submission_a_id < submission_b_id |
| **FR-16** | Similarity dimensions | MUST | `backend/app/services/similarity/*.py` | FR-14 | Phase 2 test suite | Separate exact, lexical, semantic signals |
| **FR-17** | Matched passage evidence | MUST | `backend/app/models/matched_passages.py` | FR-14 | AC-08 | Show excerpts, source, page/position, match type |
| **FR-18** | Common-content handling | MUST | `backend/app/services/content_filter.py` | FR-14 | AC-09 | Suppress question text, templates, boilerplate |
| **FR-19** | Citation/reference handling | SHOULD | `backend/app/services/citation_parser.py` | FR-14 | Phase 4 test suite | Recognize references, separate cited content |
| **FR-20** | Code analysis | SHOULD | `backend/app/services/code_analyzer.py` | FR-09 | Phase 4 test suite | Language-aware token/AST comparison |
| **FR-21** | AI-writing signal | COULD | `backend/app/services/ai_detector.py` | FR-09 | Phase 4 test suite | Experimental only, with limitations disclosure |
| **FR-22** | Grading policy | MUST | `backend/app/services/grading_service.py` | FR-12, FR-14 | Phase 3 test suite | Rubric-based marks, configurable thresholds |
| **FR-23** | Teacher override | MUST | `backend/app/api/review.py`, `backend/app/models/grading_results.py` | FR-22 | AC-10 | Edit marks, dismiss flags, record reasons |
| **FR-24** | Reports | MUST | `backend/app/services/report_generator.py` | FR-22, FR-23 | AC-13 | PDF and CSV exports |
| **FR-25** | Audit log | MUST | `backend/app/models/audit_logs.py` | All modules | AC-10, Phase 5 security testing | Record key actions with actor, timestamp |
| **FR-26** | Delete data | MUST | `backend/app/api/evaluations.py` (DELETE) | FR-25 | AC-14 | Remove files, results per retention policy |
| **FR-27** | Progress and retry | MUST | `backend/app/workers/job_manager.py` | FR-11 | AC-06 | Inspect failures, retry without duplication |
| **FR-28** | Multi-tenant isolation | MUST | `backend/app/core/auth.py`, database layer | All modules | AC-12 | Tenant checks at API and DB layers |

---

## Non-Functional Requirements Traceability

| ID | Requirement | Implementation Approach | Verification Method |
|----|-------------|------------------------|---------------------|
| **NFR-01** | Performance | Background jobs, progress tracking, benchmark 100 submissions baseline | Load testing with representative files |
| **NFR-02** | Scalability | Horizontal worker scaling, stateless API | Worker pool expansion testing |
| **NFR-03** | Reliability | Idempotent tasks, unique constraints, retry logic | Failure injection tests |
| **NFR-04** | Usability | Standalone workflow, no course setup required | User testing, manual verification |
| **NFR-05** | Explainability | Evidence excerpts, method/category labels, confidence | Manual review of outputs |
| **NFR-06** | Accessibility | Keyboard navigation, ARIA labels, contrast compliance | Automated accessibility tests (axe-core) |
| **NFR-07** | Maintainability | Modular service boundaries, interface abstractions | Code review, architecture review |
| **NFR-08** | Observability | Structured logs, job state tracking, metrics | Log aggregation, monitoring dashboards |
| **NFR-09** | Portability | Docker, environment variables, S3-compatible storage | Multi-provider deployment tests |
| **NFR-10** | Cost control | Per-evaluation feature flags, usage visibility | Usage tracking, cost reports |

---

## Acceptance Criteria Cross-Reference

| AC ID | Description | Related FR | Test Type | Phase |
|-------|-------------|-----------|-----------|-------|
| **AC-01** | ZIP ingestion creates submission records | FR-04, FR-01 | Integration | Phase 1 |
| **AC-02** | Individual files coexist with ZIP | FR-05 | Integration | Phase 1 |
| **AC-03** | Unsafe archives rejected safely | FR-06 | Security | Phase 1 |
| **AC-04** | Exactly N(N-1)/2 pairs created | FR-14 | Unit + Integration | Phase 2 |
| **AC-05** | A-B and B-A return same result | FR-15 | Unit | Phase 2 |
| **AC-06** | Idempotent retry without duplication | FR-27, FR-11 | Integration | Phase 2 |
| **AC-07** | Relevance precedes similarity | FR-12, FR-14 | State machine test | Phase 2 |
| **AC-08** | Evidence traces to source page/offset | FR-17, FR-09 | Integration | Phase 2 |
| **AC-09** | Common text excluded from overlap | FR-18 | Unit + Integration | Phase 2 |
| **AC-10** | Teacher override recorded in audit | FR-23, FR-25 | Integration | Phase 3 |
| **AC-11** | No automatic accusation | FR-21, FR-22 | Policy + Manual verification | Phase 3 |
| **AC-12** | Tenant isolation enforced | FR-28 | Security | Phase 5 |
| **AC-13** | Export matches UI values | FR-24 | Integration | Phase 3 |
| **AC-14** | Deletion removes files per policy | FR-26 | Integration | Phase 3 |

---

## Phase Mapping

| Phase | Requirements Included | Exit Criteria |
|-------|----------------------|---------------|
| **Phase 0** | Foundation setup | Documented baseline, runnable Docker environment |
| **Phase 1** | FR-01 to FR-09, FR-11, FR-28 | Teacher can upload and see extracted submissions |
| **Phase 2** | FR-12 to FR-18 | Complete text analysis report with relevance and similarity |
| **Phase 3** | FR-22 to FR-27 | Teacher can approve and export defensible results |
| **Phase 4** | FR-10, FR-19, FR-20, FR-21 | Advanced modules pass evaluation on test datasets |
| **Phase 5** | All NFRs, security hardening | Secure, supportable SaaS release |

---

## Dependencies and Constraints

### External Dependencies
- **PostgreSQL 15+**: Relational storage, unique constraints
- **Redis**: Job queue and caching
- **S3-compatible storage**: File storage (Cloudflare R2 candidate)
- **PyMuPDF, python-docx**: Document parsing
- **scikit-learn, sentence-transformers**: NLP capabilities
- **Docker, Docker Compose**: Local development environment

### Critical Path
1. **Authentication + database** (Phase 1) → blocks all features
2. **File upload + validation** (Phase 1) → blocks extraction
3. **Text extraction** (Phase 1) → blocks analysis
4. **Relevance analysis** (Phase 2) → must complete before similarity
5. **Comparison engine** (Phase 2) → blocks grading
6. **Teacher review workflow** (Phase 3) → blocks production use

---

## Open Requirements Questions

See [docs/open-questions.md](../open-questions.md) for detailed discussion of:
- Maximum ZIP/file size limits (recommend start with configurable limits)
- Student identity mapping conventions (recommend filename + optional CSV)
- Rubric behavior when omitted (recommend low-confidence warning)
- AI-writing detector provider selection (recommend defer until tested)
- Data retention duration (recommend tenant-configurable after legal review)

---

## Traceability Updates

This document will be updated as:
- Implementation modules are created
- Test suites are written
- Requirements are refined based on prototyping
- Acceptance criteria are validated

**Next review:** After Phase 1 implementation kickoff

---

## References

- [PLAGIX SRS v1.0](../PLAGIX_SRS_v1.0.pdf) - Source of truth for requirements
- [System Overview](../architecture/system-overview.md) - Architecture and component design
- [Phase Plan](../roadmap/phase-plan.md) - Detailed milestone breakdown
