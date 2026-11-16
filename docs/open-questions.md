# Open Questions and Recommendations

**PLAGIX v1.0**  
**Status:** Planning phase  
**Last updated:** 16 November 2026

---

## Purpose

This document captures unresolved decisions that the SRS leaves open or requires product/business input. Each question includes a recommended starting point to unblock implementation.

---

## Configuration and Limits

### Q1: Maximum ZIP and File Size Limits

**Question:** What should be the maximum ZIP archive size, individual file size, and file count per evaluation?

**Context:**
- Storage costs scale with file sizes
- Large files slow down processing
- Teachers may have varying needs (short essays vs. long reports)
- Need to prevent abuse while supporting legitimate use cases

**Recommendation:**
- **MVP Configuration (conservative):**
  - Maximum ZIP size: **250 MB**
  - Maximum individual file size: **50 MB**
  - Maximum file count per evaluation: **500 files**
  - Maximum total upload size per evaluation: **500 MB**

**Rationale:**
- 250 MB ZIP accommodates ~100 students × 2-5 MB PDFs
- 50 MB per file handles long reports with images
- 500 file limit protects against abuse
- All limits configurable per tenant/plan

**Next Steps:**
- Implement as configurable environment variables
- Benchmark actual processing time with representative files
- Adjust limits based on Phase 1 testing
- Document limits in API and UI

**Decision Status:** ⚠️ Pending benchmark validation

---

### Q2: Student Identity Mapping Convention

**Question:** How should the system derive student labels from filenames when no CSV mapping is provided?

**Context:**
- Teachers use inconsistent filename conventions
- Automatic mapping reduces manual work
- Incorrect mapping could assign grades to wrong student
- Some teachers may use anonymous identifiers

**Recommendation:**
- **Use multi-pattern matching with confidence scoring:**

| Filename Pattern | Derived Label | Confidence | Example |
|-----------------|---------------|------------|---------|
| `{id}_anything.ext` | Extract ID before first underscore | High | `12345_assignment.pdf` → "12345" |
| `{name}_{anything}.ext` | Extract name before first underscore | Medium | `john_doe_hw1.pdf` → "john_doe" |
| `anything_{id}.ext` | Extract ID after last underscore | Medium | `assignment_12345.pdf` → "12345" |
| `{name} - anything.ext` | Extract name before dash | Low | `John Doe - Essay.pdf` → "John Doe" |
| No pattern match | Use filename without extension | Very Low | `submission_001.pdf` → "submission_001" |

- **Features:**
  - Show confidence level in UI
  - Flag low-confidence mappings for teacher review
  - Allow teacher to edit labels before processing
  - Support CSV upload with two columns: filename, student_id
  - Warn on ambiguous/duplicate labels

**Next Steps:**
- Implement pattern matching in ingestion worker
- Add "Review Mappings" step in UI before starting analysis
- Test with real teacher filename datasets

**Decision Status:** ✅ Recommended (implement in Phase 1.3)

---

### Q3: Expected Answer Language Handling

**Question:** How should the system handle multilingual answers, language detection, and unsupported languages?

**Context:**
- SRS targets Bangla and English initially
- Students may mix languages or use other languages
- Multilingual models have varying quality across languages
- Language detection is not 100% accurate

**Recommendation:**
- **Teacher declares expected language(s) at evaluation creation:**
  - Single language: "English" or "Bangla"
  - Multilingual: "English and Bangla"
  - Any: "Mixed/Other" (lower confidence warning)

- **System behavior:**
  - Use multilingual sentence-transformers model (`paraphrase-multilingual-mpnet-base-v2`)
  - Optionally detect language per submission (langdetect library)
  - If detected language ≠ expected language: flag for review with confidence degradation
  - If language unsupported by model: mark relevance category as "uncertain" with reason

- **UI indicators:**
  - Show detected language in submission list
  - Flag language mismatches for teacher review
  - Report confidence reduction in relevance results

**Next Steps:**
- Validate multilingual model quality on Bangla test set
- Implement language detection (optional, Phase 2)
- Document supported languages in help text

**Decision Status:** ✅ Recommended (implement in Phase 2.1)

---

## Grading and Rubric

### Q4: Rubric Behavior When Omitted

**Question:** When a teacher does not provide a rubric or reference answer, what grading capabilities should the system offer?

**Context:**
- SRS states: "Relevance is not the same as factual correctness"
- Without a rubric/reference, the system cannot assess content quality
- Teachers may skip rubric to save time, expecting full auto-grading
- Need to set correct expectations

**Recommendation:**
- **When NO rubric provided:**
  - Calculate **relevance-only provisional marks** with LOW confidence
  - Scale relevance score (0.0-1.0) to max_marks
  - Show prominent warning: "No rubric provided. Marks based on question relevance only, not content correctness. Manual review strongly recommended."
  - Suggest teacher add rubric or review all marks manually

- **When rubric provided:**
  - Calculate criterion-by-criterion marks
  - Use reference answer if provided
  - Show higher confidence
  - Still require teacher review and approval

- **UI behavior:**
  - Require teacher confirmation when creating evaluation without rubric
  - Checkbox: "I understand that marks without a rubric are based on relevance only and may not reflect content quality."

**Next Steps:**
- Implement grading confidence calculation
- Add warning banners in grading results UI
- Document limitations in teacher help docs

**Decision Status:** ✅ Recommended (implement in Phase 3.1)

---

### Q5: Similarity Threshold Configuration

**Question:** What default similarity thresholds should trigger review flags, and should they be configurable?

**Context:**
- Different assignment types have different acceptable similarity levels
- Short answers may naturally have high similarity (common facts)
- Long essays should have lower similarity
- Teachers have varying tolerance levels

**Recommendation:**
- **Default thresholds (configurable per evaluation):**

| Similarity Type | High Threshold | Medium Threshold | Notes |
|----------------|----------------|------------------|-------|
| **Exact similarity** | ≥ 0.30 (30%) | ≥ 0.15 (15%) | Exact/near-exact matches trigger high flag |
| **Lexical similarity** | ≥ 0.70 (70%) | ≥ 0.50 (50%) | TF-IDF cosine similarity |
| **Semantic similarity** | ≥ 0.85 (85%) | ≥ 0.70 (70%) | Embedding cosine similarity |

- **Behavior:**
  - High threshold: Flag for immediate review, mark in red
  - Medium threshold: Mark in yellow, suggest review
  - Below medium: No flag

- **UI configuration:**
  - Show threshold sliders in evaluation settings (advanced)
  - Provide presets: "Strict", "Moderate" (default), "Lenient"
  - Explain what each threshold means

**Next Steps:**
- Validate thresholds on test dataset (Phase 2 validation)
- Measure false-positive and false-negative rates
- Adjust based on teacher feedback in beta

**Decision Status:** ⚠️ Pending test dataset validation

---

## Advanced Features

### Q6: AI-Writing Detector Provider Selection

**Question:** Which AI-writing detection method should be used, and how should it be integrated?

**Context:**
- AI-writing detectors are unreliable (high false-positive rates)
- External APIs are expensive and raise privacy concerns
- Open-source detectors have varying quality
- SRS requires this to be experimental and cautious

**Recommendation:**
- **DO NOT integrate AI-writing detector in MVP (Phase 1-3)**
- **Phase 4 approach (experimental):**
  - Research open-source detectors (GPTZero alternatives, statistical methods)
  - Test on diverse student writing samples (Bangla + English)
  - Measure false-positive rate (target: document explicitly, aim for <20%)
  - Implement as opt-in feature (teacher enables per evaluation)
  - Show result with:
    - Confidence score
    - Model/version used
    - Prominent disclaimer: "This is NOT proof of AI authorship. False positives are common. Use only as one input for teacher judgment."
  - Never auto-deduct marks or label student as dishonest

- **If no reliable detector found:**
  - Skip this feature entirely
  - Document decision in ADR

**Next Steps:**
- Defer until Phase 4
- Conduct literature review on detector accuracy
- Test on representative Bangla/English student samples
- Document false-positive rate prominently

**Decision Status:** ⚠️ Deferred to Phase 4, ethical review required

---

### Q7: OCR Engine Selection

**Question:** Which OCR engine should be used for scanned PDFs?

**Context:**
- Tesseract is open-source but requires installation and language packs
- Cloud OCR APIs (Google Vision, AWS Textract) are accurate but expensive
- OCR quality varies by language and document quality
- OCR is Phase 4 (optional for MVP)

**Recommendation:**
- **Phase 4 approach:**

| Option | Pros | Cons | Cost (100 pages) |
|--------|------|------|------------------|
| **Tesseract (local)** | Free, no privacy concerns | Slower, lower accuracy, requires language packs | $0 |
| **Google Vision API** | High accuracy, multi-language | Privacy concerns, cost per page | ~$0.15 |
| **AWS Textract** | High accuracy, AWS ecosystem | Cost per page, AWS lock-in | ~$0.15 |

- **Recommended starting point:** Tesseract + Bangla language pack
  - Test accuracy on sample scanned PDFs
  - If accuracy <80%, evaluate cloud APIs with teacher consent
  - Store OCR confidence per page
  - Flag low-confidence (<70%) pages for manual review
  - Never silently use uncertain OCR for high-stakes decisions

**Next Steps:**
- Defer until Phase 4
- Create test set of scanned Bangla/English PDFs
- Benchmark Tesseract accuracy
- Document limitations

**Decision Status:** ⚠️ Deferred to Phase 4, benchmark required

---

### Q8: Code Language Support

**Question:** Which programming languages should be supported for code similarity analysis?

**Context:**
- Code analysis is Phase 4 (optional)
- Different languages require different parsers
- AST parsing adds complexity
- Token-based comparison is language-agnostic but less accurate

**Recommendation:**
- **Phase 4 initial support:**
  - **Python** (most common in education)
  - **C/C++** (algorithms and systems courses)
  - **Java** (CS fundamentals)

- **Approach:**
  - Use language-specific tokenizers (pygments or tree-sitter)
  - Normalize identifiers (rename variables to generic names)
  - Compare token n-grams (fast, language-agnostic)
  - Optionally parse AST for structural similarity (Python: ast module, C++: tree-sitter)
  - Show matched code spans with line numbers

- **Future languages:**
  - JavaScript/TypeScript
  - SQL
  - MATLAB
  - Add based on teacher demand

**Next Steps:**
- Defer until Phase 4
- Test on code plagiarism dataset (MOSS, CodeNet)
- Handle common starter code (exclude or mark)
- Document limitations for trivial solutions

**Decision Status:** ⚠️ Deferred to Phase 4

---

## Data and Privacy

### Q9: Data Retention Duration

**Question:** How long should evaluation data (files, results, reports) be retained before deletion?

**Context:**
- Academic records may have institutional retention requirements
- Storage costs scale with retention
- Students may appeal grades months later
- GDPR/privacy laws may require deletion on request

**Recommendation:**
- **Configurable per tenant with sane defaults:**
  - **Immediate deletion:** Test evaluations (manual trigger)
  - **30-day retention:** Default for MVP (automatic after 30 days)
  - **90-day retention:** Recommended for production (covers appeal period)
  - **1-year retention:** Enterprise/institutional plan
  - **Custom retention:** Per tenant configuration

- **Implementation:**
  - Soft delete on teacher request (mark deleted_at, hide in UI)
  - Background job: hard delete after retention period
  - Preserve minimal audit trail (evaluation ID, teacher, date) indefinitely
  - Allow manual deletion anytime (teacher or admin)

- **Compliance:**
  - Honor deletion requests immediately (GDPR right to erasure)
  - Document retention policy in privacy policy
  - Notify teachers before auto-deletion

**Next Steps:**
- Implement soft delete in Phase 3
- Implement retention policy in Phase 5
- Consult legal/compliance on institutional requirements

**Decision Status:** ⚠️ Pending legal review, implement 30-day default

---

### Q10: Anonymous vs. Named Submissions

**Question:** Should the system support anonymous submissions (blind grading)?

**Context:**
- Blind grading reduces bias
- Some teachers want to know student identities upfront
- Plagiarism detection requires linking identities eventually
- Phase 1 uses filename-based labels

**Recommendation:**
- **Phase 1-3:** Named submissions (student labels visible)
- **Future enhancement (post-MVP):**
  - Add "blind grading" mode at evaluation creation
  - System generates anonymous IDs (Student A, Student B, etc.)
  - Teacher reviews and grades without seeing names
  - After approval, teacher "unblind" to see identities
  - Useful for fairness in grading, less critical for plagiarism detection

**Next Steps:**
- Not required for MVP
- Gather teacher feedback in beta
- Implement if demand is high

**Decision Status:** ✅ Defer to post-MVP

---

## Hosting and Deployment

### Q11: Hosting Provider Selection

**Question:** Which hosting providers should be used for API, database, storage, and workers?

**Context:**
- Cost is critical for bootstrapped SaaS
- Free tiers vary by provider
- Data residency may matter for institutional customers
- Avoid vendor lock-in where possible

**Recommendation:**
- **MVP Hosting Stack (optimize for free tiers):**

| Service | Provider (Primary) | Provider (Alternative) | Cost (MVP) |
|---------|-------------------|----------------------|-----------|
| **API & Workers** | Railway / Render | Fly.io | $0-5/month |
| **PostgreSQL** | Neon / Supabase | Railway Postgres | $0 (free tier) |
| **Redis** | Upstash | Railway Redis | $0 (free tier) |
| **Object Storage** | Cloudflare R2 | Backblaze B2 | $0 (10GB free) |
| **Frontend** | Vercel / Cloudflare Pages | Netlify | $0 |

- **Rationale:**
  - All support Docker deployment (portability)
  - Free tiers cover MVP needs (low user count)
  - S3-compatible storage (easy to switch)
  - Managed services reduce operational burden

- **Migration path:**
  - Phase 5: Evaluate AWS/GCP/Azure for enterprise
  - Keep infrastructure-as-code for easy migration

**Next Steps:**
- Set up staging environment with recommended stack
- Benchmark performance and costs
- Document deployment process
- Keep deployment scripts provider-agnostic (Docker)

**Decision Status:** ✅ Recommended for MVP (finalize in Phase 5)

---

### Q12: Data Region and Compliance

**Question:** Where should data be stored, and what compliance requirements apply?

**Context:**
- Target users: Initially Bangladesh and global teachers
- GDPR applies if EU users access the platform
- Some institutions require data to stay in specific regions
- Compliance certifications (SOC 2, ISO 27001) are expensive

**Recommendation:**
- **MVP (Phase 1-4):**
  - Store data in single region (US or EU, provider default)
  - No compliance certifications required for MVP
  - Document data handling in privacy policy
  - Implement basic GDPR rights (access, deletion)

- **Production (Phase 5):**
  - Offer region selection for enterprise customers
  - Implement data residency controls
  - Consider SOC 2 Type II certification (if enterprise demand)
  - Consult legal on FERPA (US education data) and BDPA (Bangladesh) if applicable

**Next Steps:**
- Draft privacy policy during Phase 5
- Consult legal counsel before public launch
- Implement user data export (GDPR right to portability)

**Decision Status:** ⚠️ Pending legal review, defer to Phase 5

---

## Implementation Priorities

### Q13: Feature Priority Trade-offs

**Question:** If development is slower than expected, which features can be deferred beyond MVP?

**Context:**
- Time to market is critical
- Some features are "nice to have" vs. "must have"
- Need flexibility for scope adjustment

**Recommendation:**
- **Must Have (MVP):**
  - Upload, extraction, text similarity, teacher review (Phase 1-3)
  - Cannot launch without these

- **Should Have (defer if needed):**
  - Semantic similarity (can launch with lexical only)
  - Individual reports (batch summary may be sufficient)
  - Real-time progress (can use polling instead of WebSocket)

- **Nice to Have (Phase 4+):**
  - OCR (digital PDFs cover 90% of use cases)
  - Code similarity (target specific teachers with code assignments)
  - AI-writing detection (unreliable, low value)
  - Citation parsing (can manually review)

**Next Steps:**
- Re-evaluate scope after Phase 1 completion
- Track velocity and adjust roadmap
- Communicate trade-offs to stakeholders

**Decision Status:** ✅ Recommended prioritization

---

## Summary of Recommendations

| Question | Status | Recommended Action |
|----------|--------|-------------------|
| Q1: File size limits | ⚠️ Benchmark | Start with 250MB ZIP, 50MB file, 500 count |
| Q2: Student mapping | ✅ Implement | Pattern matching with confidence scoring |
| Q3: Language handling | ✅ Implement | Teacher declares, system detects, flags mismatches |
| Q4: No-rubric grading | ✅ Implement | Low-confidence relevance-only marks with warning |
| Q5: Similarity thresholds | ⚠️ Validate | Default: 30% exact, 70% lexical, 85% semantic |
| Q6: AI-writing detector | ⚠️ Defer Phase 4 | Do not include in MVP, research in Phase 4 |
| Q7: OCR engine | ⚠️ Defer Phase 4 | Start with Tesseract, evaluate cloud if needed |
| Q8: Code languages | ⚠️ Defer Phase 4 | Python, C++, Java initially |
| Q9: Data retention | ⚠️ Legal review | 30-day default, configurable, honor delete requests |
| Q10: Anonymous grading | ✅ Defer | Post-MVP feature based on teacher demand |
| Q11: Hosting providers | ✅ Recommended | Railway/Render + Neon + R2 + Vercel for MVP |
| Q12: Data region | ⚠️ Legal review | Single region for MVP, multi-region in Phase 5 |
| Q13: Feature priority | ✅ Recommended | Must: upload+similarity+review; defer: OCR, code, AI |

---

## Decision Log

| Date | Question | Decision | Rationale |
|------|----------|----------|-----------|
| 2026-11-16 | Student mapping | Pattern matching + confidence | Balances automation and accuracy |
| 2026-11-16 | AI detector in MVP | No | Unreliable, defer to Phase 4 with ethical review |
| 2026-11-16 | Hosting stack | Railway + Neon + R2 | Free tiers, portability, managed services |

---

## Next Steps

1. **Week 1 (Phase 0 completion):**
   - Review and approve all recommendations
   - Finalize file size limits after benchmark
   - Begin implementing student mapping logic

2. **Phase 1:**
   - Validate student mapping with real teacher datasets
   - Test language detection accuracy on Bangla samples

3. **Phase 2:**
   - Validate similarity thresholds on test dataset
   - Document false-positive/false-negative rates

4. **Phase 4:**
   - Research AI-writing detectors (ethical review)
   - Test OCR accuracy on scanned PDFs
   - Implement code similarity if teacher demand exists

5. **Phase 5:**
   - Legal review of privacy policy and data retention
   - Finalize hosting provider and data region
   - Implement compliance requirements

---

## References

- [PLAGIX SRS v1.0](PLAGIX_SRS_v1.0.pdf) - Requirements baseline
- [Requirements Traceability](requirements/requirements-traceability.md) - FR mapping
- [ADR-0001: Technology Stack](decisions/ADR-0001-technology-stack.md) - Stack rationale
- [Phase Plan](roadmap/phase-plan.md) - Implementation roadmap

---

**Status:** Open questions documented with recommendations. Ready for stakeholder review and Phase 0 implementation kickoff.
