# ADR-0001: Technology Stack Selection

**Status:** Accepted  
**Date:** 16 November 2026  
**Decision makers:** Product architect, engineering lead  
**Context:** Phase 0 planning for PLAGIX MVP

---

## Context and Problem Statement

PLAGIX is a standalone SaaS platform for academic answer evaluation and integrity checking. The system must handle file uploads, document processing, NLP analysis, pairwise comparisons, and teacher review workflows. We need to select a technology stack that balances:

- **Developer productivity** (rapid MVP delivery)
- **Performance** (handle 100+ submissions with 4,950 pairwise comparisons)
- **Scalability** (horizontal scaling of workers and API)
- **Security** (tenant isolation, safe file handling, audit trails)
- **Maintainability** (clear module boundaries, testability)
- **Cost** (optimize for free/low-cost tiers during MVP)
- **Multilingual support** (Bangla and English text processing)

---

## Decision Drivers

1. **Time to MVP**: Need functional prototype in 4-6 weeks
2. **Background processing**: Long-running tasks (extraction, comparison) must not block UI
3. **NLP capabilities**: Require TF-IDF, embeddings, multilingual models
4. **File safety**: Must safely handle ZIP bombs, path traversal, malformed documents
5. **Tenant isolation**: Multi-tenant SaaS requires strict data boundaries
6. **Algorithm flexibility**: Similarity implementations should be replaceable
7. **Deployment flexibility**: Avoid vendor lock-in; support multiple hosting providers
8. **Open source preference**: Minimize proprietary dependencies in MVP

---

## Considered Options

### Frontend
- **Option A**: Next.js (React) + TypeScript
- **Option B**: Vue.js + Nuxt + TypeScript
- **Option C**: SvelteKit + TypeScript
- **Option D**: Django templates (server-rendered)

### Backend API
- **Option A**: Python + FastAPI
- **Option B**: Python + Django REST Framework
- **Option C**: Node.js + Express + TypeScript
- **Option D**: Go + Gin

### Database
- **Option A**: PostgreSQL
- **Option B**: MySQL
- **Option C**: MongoDB
- **Option D**: SQLite (development only)

### Background Jobs
- **Option A**: Redis + Celery (Python)
- **Option B**: RabbitMQ + Celery (Python)
- **Option C**: Bull (Node.js)
- **Option D**: Temporal (workflow engine)

### NLP/ML Libraries
- **Option A**: scikit-learn + sentence-transformers (Python)
- **Option B**: spaCy + transformers (Python)
- **Option C**: TensorFlow.js (Node.js)
- **Option D**: External API (OpenAI, Cohere)

---

## Decision Outcome

### Selected Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | Next.js + TypeScript | 14+ |
| **UI Components** | Tailwind CSS + shadcn/ui | Latest |
| **Backend API** | Python + FastAPI | 3.11+ / 0.104+ |
| **Database** | PostgreSQL | 15+ |
| **Vector Extension** | pgvector | 0.5+ (Phase 4) |
| **Background Jobs** | Redis + Celery | 7+ / 5.3+ |
| **Document Processing** | PyMuPDF, python-docx | Latest |
| **NLP** | scikit-learn, sentence-transformers | Latest |
| **Object Storage** | S3-compatible (Cloudflare R2) | N/A |
| **Containerization** | Docker + Docker Compose | 24+ |
| **CI/CD** | GitHub Actions | N/A |

---

## Rationale

### Frontend: Next.js + TypeScript

**Why Next.js:**
- **React ecosystem**: Large community, extensive component libraries (shadcn/ui)
- **TypeScript**: Type safety reduces bugs in complex workflows
- **App Router**: Modern routing with server components for initial page loads
- **API routes**: Can proxy sensitive operations without exposing secrets to client
- **Deployment**: Vercel, Netlify, Cloudflare Pages (generous free tiers)

**Why not Vue/Svelte:**
- Smaller ecosystem for accessibility-focused component libraries
- Team familiarity with React

**Why not Django templates:**
- Poor interactivity for real-time progress tracking and rich UI
- Harder to componentize complex review workflows

---

### Backend: Python + FastAPI

**Why FastAPI:**
- **Performance**: Async support, comparable to Node.js for I/O-bound tasks
- **Developer experience**: Automatic OpenAPI docs, Pydantic validation, type hints
- **Python ecosystem**: Direct access to NLP libraries (scikit-learn, sentence-transformers, PyMuPDF)
- **Validation**: Pydantic models catch errors early
- **Async/await**: Natural fit for database queries and external API calls

**Why not Django REST Framework:**
- Heavier framework, slower prototyping
- Celery integration is mature in both, but FastAPI is lighter

**Why not Node.js:**
- NLP libraries (TF-IDF, embeddings) are more mature in Python
- Would require calling Python scripts from Node.js for analysis (added complexity)

**Why not Go:**
- NLP ecosystem is immature
- Slower MVP development (more boilerplate)

---

### Database: PostgreSQL

**Why PostgreSQL:**
- **ACID compliance**: Critical for financial/academic data integrity
- **Unique constraints**: Enforce canonical pair storage (`submission_a_id < submission_b_id`)
- **JSONB**: Flexible storage for rubric criteria, evidence, metadata
- **pgvector**: Native vector similarity search (Phase 4 semantic retrieval)
- **Full-text search**: Built-in capabilities for future content search
- **Row-level security**: Can enforce tenant isolation at DB level (Phase 5)
- **Mature tooling**: Alembic migrations, SQLAlchemy ORM, pgAdmin

**Why not MySQL:**
- Weaker JSON support compared to PostgreSQL JSONB
- No native vector extension

**Why not MongoDB:**
- Relational data model is a better fit (foreign keys, joins, constraints)
- Harder to enforce uniqueness constraints for canonical pairs
- ACID transactions are critical

---

### Background Jobs: Redis + Celery

**Why Redis + Celery:**
- **Battle-tested**: Celery is the standard for Python background tasks
- **Horizontal scaling**: Add more workers without code changes
- **Task routing**: Route different task types to specialized workers
- **Retry logic**: Built-in exponential backoff, max retries
- **Monitoring**: Flower dashboard for task visibility
- **Redis**: Fast, simple, doubles as cache for evaluation metadata

**Why not RabbitMQ:**
- Redis is simpler to deploy and operate for MVP
- RabbitMQ is overkill for initial scale

**Why not Bull (Node.js):**
- Backend is Python; keeping job queue in same language simplifies deployment

**Why not Temporal:**
- Overkill for MVP; adds operational complexity
- Can migrate to Temporal in Phase 5 if workflow complexity justifies it

---

### NLP: scikit-learn + sentence-transformers

**Why scikit-learn:**
- **TF-IDF**: Standard, explainable, fast for lexical similarity
- **Cosine similarity**: Efficient pairwise comparison
- **Mature**: Well-tested, stable API

**Why sentence-transformers:**
- **Multilingual models**: `paraphrase-multilingual-mpnet-base-v2` supports Bangla + English
- **Semantic similarity**: State-of-the-art for paraphrase detection
- **Sentence embeddings**: Can store in pgvector for retrieval (Phase 4)
- **Local inference**: No external API dependency, no per-request cost
- **Open source**: No licensing restrictions

**Why not spaCy:**
- Heavier, slower loading
- sentence-transformers is specialized for semantic similarity

**Why not external API (OpenAI, Cohere):**
- **Cost**: Per-request pricing adds up quickly (100 submissions × 4,950 pairs × $0.0001 = $49.50 per evaluation)
- **Privacy**: Sending student answers to third-party raises concerns
- **Latency**: Network round-trips slow down batch processing
- **Dependency**: External API outages block processing
- **Lock-in**: Hard to switch providers mid-deployment

**Decision**: Use local models for MVP; evaluate external APIs for advanced features (rubric grading, AI-writing detection) in Phase 4 with explicit teacher consent.

---

### Document Processing: PyMuPDF + python-docx

**Why PyMuPDF (fitz):**
- **Fast**: C++ backend, handles large PDFs efficiently
- **Text extraction**: Preserves page boundaries and offsets
- **Block detection**: Identifies paragraphs for chunking
- **Scanned PDF detection**: Low selectable text triggers OCR path
- **License**: AGPL (acceptable for SaaS with proper compliance)

**Why python-docx:**
- **Standard**: De facto library for DOCX parsing
- **Paragraph access**: Preserves document structure
- **Reliable**: Mature, well-maintained

**Why not PDFMiner, pdfplumber:**
- Slower than PyMuPDF for large batches
- pdfplumber is better for tables (not primary MVP use case)

---

### Object Storage: S3-compatible (Cloudflare R2 candidate)

**Why S3-compatible:**
- **Standard API**: Easy to switch providers (AWS S3, Cloudflare R2, MinIO, Backblaze B2)
- **No egress fees** (Cloudflare R2): Critical cost advantage
- **Scalability**: Handle large files without local disk
- **Presigned URLs**: Secure time-limited downloads without proxying
- **Lifecycle policies**: Automatic deletion per retention rules

**Why Cloudflare R2 (candidate):**
- **Zero egress fees**: Save 90% compared to AWS S3
- **S3 API compatibility**: Drop-in replacement
- **Free tier**: 10 GB storage, 1M Class A operations/month
- **Global CDN**: Fast downloads for teachers

**Alternative**: MinIO for local development (S3-compatible, Docker container)

---

### Containerization: Docker + Docker Compose

**Why Docker:**
- **Reproducible environments**: Dev/staging/prod consistency
- **Dependency isolation**: Python, Node.js, PostgreSQL, Redis in separate containers
- **Easy onboarding**: `docker-compose up` starts entire stack
- **Deployment flexibility**: Deploy to any container host (Render, Fly.io, Railway, AWS ECS)

**Why Docker Compose:**
- **Local development**: Single file defines all services
- **Networking**: Automatic service discovery
- **Volume management**: Persist database and Redis data

---

### CI/CD: GitHub Actions

**Why GitHub Actions:**
- **Integrated**: Runs in same platform as code
- **Free tier**: 2,000 minutes/month for private repos
- **Matrix builds**: Test multiple Python/Node versions
- **Artifact storage**: Cache dependencies, store build outputs
- **Deployment**: Can deploy to Vercel, Render, etc. from Actions

**Typical workflow:**
1. Run linters (Ruff, ESLint)
2. Run type checkers (mypy, TypeScript)
3. Run unit tests (pytest, Jest)
4. Build Docker images
5. Deploy to staging on `main` push
6. Deploy to production on tagged release

---

## Consequences

### Positive

- **Rapid prototyping**: FastAPI + Next.js enable fast iteration
- **Type safety**: TypeScript + Pydantic reduce runtime errors
- **Explainability**: TF-IDF and local models are transparent
- **Cost efficiency**: Local NLP inference, zero egress fees (R2)
- **Scalability**: Horizontal worker scaling, stateless API
- **Flexibility**: Can swap algorithms, storage providers, deployment targets
- **Security**: Strong isolation (containers), safe file handling (Python libraries)

### Negative

- **GPU acceleration**: sentence-transformers is faster with GPU, but MVP uses CPU (acceptable for <100 submissions)
- **Learning curve**: Team must know Python, TypeScript, React, PostgreSQL, Celery
- **Operational complexity**: Multiple services (API, workers, DB, Redis, storage) to monitor

### Neutral

- **Python/Node.js split**: Frontend and backend in different languages, but common in modern stacks
- **Docker dependency**: Requires Docker knowledge, but widely adopted

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| sentence-transformers inference too slow | Benchmark early; add GPU worker or switch to lighter model if needed |
| Celery tasks fail silently | Implement monitoring (Flower), alerting, dead-letter queue |
| PostgreSQL becomes bottleneck | Add read replicas, connection pooling (PgBouncer) in Phase 5 |
| Vendor lock-in (Cloudflare R2) | Use S3-compatible API; easy to switch to AWS/Backblaze |
| PyMuPDF license (AGPL) | Ensure SaaS usage complies; alternative is pdfplumber (MIT) |

---

## Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Use external AI API for relevance/grading? | **No** for MVP; evaluate in Phase 4 with teacher consent |
| GPU for sentence-transformers? | **No** for MVP; CPU sufficient for <100 submissions; revisit at scale |
| Row-level security in PostgreSQL? | **No** for MVP; enforce in application layer; add RLS in Phase 5 |
| Soft delete or hard delete? | **Hard delete** in MVP with audit trail; add soft delete in Phase 5 |

---

## Alternatives Considered and Rejected

### Full-Stack Framework (Django + HTMX)

**Pros:**
- Single language (Python)
- Simpler deployment (one monolith)

**Cons:**
- Poor interactivity for real-time progress
- Harder to scale frontend independently
- HTMX is less mature than React for complex UIs

**Verdict:** Rejected for poor UX on interactive workflows

---

### Serverless Functions (AWS Lambda)

**Pros:**
- No server management
- Pay-per-request pricing

**Cons:**
- Cold start latency (critical for NLP models)
- Timeout limits (15 min max for Lambda)
- Harder to debug long-running comparisons
- Vendor lock-in (hard to migrate)

**Verdict:** Rejected; not suitable for long-running NLP tasks

---

### NoSQL Database (MongoDB)

**Pros:**
- Flexible schema for varied rubric structures

**Cons:**
- Weak support for unique constraints (canonical pairs)
- ACID transactions less mature than PostgreSQL
- Joins are inefficient (common in evaluation queries)

**Verdict:** Rejected; relational model is better fit

---

### External AI API (OpenAI GPT-4 for grading)

**Pros:**
- State-of-the-art reasoning for rubric grading
- Less code to maintain

**Cons:**
- **Cost**: $0.01 per submission × 100 submissions = $1 per evaluation (unsustainable at scale)
- **Privacy**: Student answers sent to third party
- **Latency**: Network round-trips slow batch processing
- **Reliability**: API outages block grading

**Verdict:** Rejected for MVP; consider as opt-in feature in Phase 4

---

## References

- [PLAGIX SRS v1.0](../PLAGIX_SRS_v1.0.pdf) - Requirements baseline
- [System Overview](../architecture/system-overview.md) - Architecture context
- FastAPI Documentation: https://fastapi.tiangolo.com/
- sentence-transformers: https://www.sbert.net/
- Celery Documentation: https://docs.celeryq.dev/
- pgvector: https://github.com/pgvector/pgvector
- Cloudflare R2: https://developers.cloudflare.com/r2/

---

## Review and Update

This ADR should be reviewed:
- After Phase 1 MVP completion (validate performance assumptions)
- Before Phase 4 (evaluate GPU, external APIs, advanced NLP)
- Before Phase 5 (evaluate move to Temporal, RLS, managed services)

**Next ADR:** ADR-0002 will address authentication strategy (session-based vs. JWT vs. OAuth)

---

## Approval

- [x] Product architect: Approved
- [x] Engineering lead: Approved
- [ ] Security review: Pending Phase 1 implementation
- [ ] Cost analysis: Pending Phase 1 benchmarking
