# File Upload Experience Specification

**PLAGIX v1.0**  
**Last updated:** 21 November 2026

---

## Upload Capabilities

PLAGIX supports mixed batch uploads in a single evaluation job:
- **Bulk ZIP archive** containing multiple student submission files.
- **Multiple individual PDF files**.
- **DOCX and TXT files**.
- **Mixture of ZIP and individual files** combined.

---

## Upload UX & Validation

### Dropzone Requirements
- Visual drag-and-drop target with clear instructions.
- File browser fallback button (`[Browse Files]`).
- Allowed extension badges (PDF, DOCX, TXT, ZIP).

### Safety & Validation Rules
1. **File Type Verification:** MIME type check against magic bytes (not just extension).
2. **Size Limits:** Max 50 MB per individual file, max 250 MB per ZIP archive.
3. **Archive Safety:** Safe ZIP extraction preventing path traversal (`../`), ZIP bombs (compression ratio checks), and symlink injection.
4. **Duplicate Detection:** SHA-256 hash computed per file to warn teacher of duplicate uploads.
5. **Progress Feedback:** Real-time upload progress percentage and per-file extraction status.

---
