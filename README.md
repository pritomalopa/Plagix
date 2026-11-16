# PLAGIX

**Academic Answer Evaluation & Integrity Platform**

Version: 0.1.0-planning  
Status: Architecture & planning phase  
Last updated: 16 November 2026

---

## Product Summary

PLAGIX is a standalone SaaS utility that helps teachers evaluate batches of student assignment submissions. Teachers create an evaluation job, provide the question and optional rubric, upload student answers (ZIP or individual files), and receive an explainable analysis of answer relevance, text similarity, and provisional marks for review.

**PLAGIX does NOT:**
- Manage courses, classes, rosters, or attendance
- Distribute assignments or replace Google Classroom/Moodle/LMS
- Require students to register accounts in the MVP
- Automatically accuse students or deduct marks based on similarity/AI signals alone

**PLAGIX DOES:**
- Accept bulk ZIP uploads or individual PDF/DOCX/TXT files
- Validate and safely extract submissions
- Evaluate answer relevance FIRST against the provided question
- Perform unique within-batch pairwise similarity analysis (N×(N-1)/2 comparisons)
- Show explainable matched passages and evidence
- Generate provisional marks based on rubric (when provided)
- Allow teacher review, override, and approval of all results
- Maintain audit trails and support data deletion

---

## Product Scope

### In Scope (MVP)
- Teacher authentication and evaluation creation
- Question input, rubric, reference answer, expected concepts
- ZIP + individual file upload in the same job
- Safe archive extraction with malicious-file protection
- Text extraction from PDF/DOCX/TXT with offset preservation
- Answer relevance analysis before similarity checking
- Canonical pairwise comparison with uniqueness constraint
- Explainable similarity evidence (exact, lexical, semantic)
- Common-content and template handling
- Teacher review, mark override, and audit logging
- PDF/CSV report export
- Multi-tenant isolation

### Future Phases
- OCR for scanned PDFs (Phase 4)
- Code similarity analysis (Phase 4)
- Cautious AI-writing indicators (Phase 4, experimental only)
- Citation/reference parsing (Phase 4)
- Semantic embeddings and MinHash/LSH optimization (Phase 4)
- Cross-batch historical comparison (post-MVP)
- Student portal (post-MVP)

---

## Technology Stack (Planned)

**Status: Architecture recommendations; not yet implemented.**

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14+, TypeScript, Tailwind CSS, shadcn/ui | Teacher dashboard, evaluation setup, upload UI, review interface |
| **Backend API** | Python 3.11+, FastAPI, Pydantic | REST API, validation, orchestration, authentication |
| **Database** | PostgreSQL 15+, SQLAlchemy, Alembic | Relational data, tenant isolation, canonical pair storage |
| **Vector Search** | pgvector (optional, Phase 4) | Semantic similarity retrieval when needed |
| **Background Jobs** | Redis, Celery | Async processing: extraction, analysis, comparisons |
| **Document Processing** | PyMuPDF, python-docx | PDF/DOCX/TXT text extraction with offsets |
| **NLP/Analysis** | scikit-learn, sentence-transformers | TF-IDF, n-grams, embeddings, Winnowing |
| **Object Storage** | S3-compatible (Cloudflare R2 candidate) | Uploaded files, generated reports |
| **Containerization** | Docker, Docker Compose | Local dev, reproducible environments |
| **CI/CD** | GitHub Actions | Automated tests, linting, build checks |

### Technology Selection Principles
- **Modular monolith first**: clear internal boundaries, avoid premature microservices
- **Replaceable algorithms**: keep similarity/relevance implementations behind interfaces
- **Hosting flexibility**: Docker-based deployment, provider-agnostic configuration
- **Cost awareness**: enable AI/embedding features per evaluation, not globally mandatory
- **Security by default**: tenant isolation, safe ZIP handling, secrets management, audit logging

---

## Project Structure (Planned)

```
plagix/
├── frontend/                 # Next.js application (NOT YET CREATED)
│   ├── src/
│   │   ├── app/             # App router pages
│   │   ├── components/       # React components
│   │   └── lib/             # Utilities, API client
│   └── package.json
├── backend/                  # FastAPI application (NOT YET CREATED)
│   ├── app/
│   │   ├── api/             # API routes
│   │   ├── core/            # Config, auth, database
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   └── workers/         # Celery tasks
│   ├── alembic/             # Database migrations
│   ├── tests/
│   └── requirements.txt
├── docs/
│   ├── PLAGIX_SRS_v1.0.pdf  # Source of truth for requirements
│   ├── PLAGIX_SRS_v1.0.txt  # Extracted text for tooling
│   ├── requirements/        # Requirements traceability
│   ├── architecture/        # System design, data model, pipeline
│   ├── decisions/           # Architecture Decision Records
│   └── roadmap/             # Phase plans, milestones
├── docker-compose.yml        # Local development stack (NOT YET CREATED)
├── .github/workflows/        # CI configuration (NOT YET CREATED)
└── README.md                # This file
```

---

## Architecture Highlights

### End-to-End Workflow
1. **Create evaluation** → Teacher enters question, rubric, marking criteria
2. **Upload submissions** → ZIP or individual files, with validation
3. **Validate & extract** → Safe ZIP extraction, file type/size checks
4. **Extract text** → Parse PDF/DOCX/TXT, preserve page/offset for evidence
5. **Check relevance FIRST** → Evaluate each answer against the question
6. **Compare submissions** → Unique pairwise analysis (N×(N-1)/2)
7. **Generate provisional marks** → Rubric-based scoring with evidence
8. **Teacher review** → Inspect, override, approve, record reasons
9. **Export reports** → PDF and CSV with explainable results

### Fairness and Correctness Rules
- **Relevance ≠ correctness**: A rubric improves quality; without one, don't claim full grading capability
- **Similarity ≠ plagiarism**: Show evidence for human review, not automatic accusations
- **Canonical pair storage**: `submission_a_id < submission_b_id` with unique constraint on `(evaluation_id, submission_a_id, submission_b_id)`
- **Symmetric comparisons**: A-B and B-A resolve to the same stored result
- **Separate dimensions**: Keep relevance, content marks, text similarity, code similarity, AI signals, and final marks distinct
- **Teacher authority**: Teacher must inspect evidence, override marks, dismiss flags, and record reasons

### Security and Privacy
- Tenant isolation at API and database layers
- Safe ZIP extraction (defend against path traversal, ZIP bombs, symlinks)
- Malicious file validation (MIME/signature checks, size limits)
- Secrets in environment variables, never in Git
- HTTPS in transit, encryption at rest
- Audit logging for file access, grade changes, deletions
- Configurable data retention and deletion workflows

---

## Development Status

**Phase 0 - Foundation: IN PROGRESS**

- [x] SRS document created and extracted to text
- [x] README.md drafted
- [ ] Requirements traceability matrix
- [ ] Architecture diagrams and system overview
- [ ] Data model with ERD
- [ ] Processing pipeline design
- [ ] Technology stack ADR
- [ ] Phase plan and milestones
- [ ] Open questions documented
- [ ] Local Docker environment
- [ ] Database schema and migrations
- [ ] CI/CD skeleton
- [ ] Authentication scaffold

**Nothing has been implemented yet.** This README describes the planned architecture based on the SRS requirements.

---

## Getting Started (Planned)

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and npm (for frontend development)
- Python 3.11+ (for backend development)
- Git

### Local Development (NOT YET AVAILABLE)
```bash
# Clone the repository
git clone <repository-url>
cd plagix

# Start services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access services
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## Testing (Planned)

### Test Dataset Design
- Exact-copy pair
- Near-copy with edits
- Paraphrase pair
- Common-prompt pair
- Citation pair with references
- Unrelated pair
- Short-answer pair
- Bangla/English multilingual pair
- OCR pair (scanned + digital)
- Code pair with renamed identifiers

### Evaluation Metrics
- Precision, recall, false-positive rate, false-negative rate
- Human-reviewer agreement on relevance categories
- OCR extraction quality
- AI-writing detector calibration on representative student writing

---

## Documentation

| Document | Purpose |
|----------|---------|
| [SRS v1.0](docs/PLAGIX_SRS_v1.0.pdf) | Complete software requirements specification (source of truth) |
| [Requirements Traceability](docs/requirements/requirements-traceability.md) | Functional requirements mapped to modules and tests |
| [System Overview](docs/architecture/system-overview.md) | Logical components, boundaries, workflow diagrams |
| [Data Model](docs/architecture/data-model.md) | Entities, relationships, indexes, canonical pair storage |
| [Processing Pipeline](docs/architecture/processing-pipeline.md) | Upload → extraction → relevance → comparison → grading flow |
| [ADR-0001: Technology Stack](docs/decisions/ADR-0001-technology-stack.md) | Stack selection rationale |
| [Phase Plan](docs/roadmap/phase-plan.md) | MVP milestones and delivery roadmap |
| [Open Questions](docs/open-questions.md) | Unresolved decisions with recommendations |

---

## Contributing (Future)

This project is currently in planning phase. Contribution guidelines will be added once the foundation is established.

---

## License

[To be determined]

---

## Contact

[To be determined]

---

**IMPORTANT**: PLAGIX is designed as an evaluation assistant, not a replacement for teacher judgment. Similarity analysis and AI-writing indicators are review signals, not proof of misconduct. Teachers must review evidence, approve marks, and make final academic decisions.
