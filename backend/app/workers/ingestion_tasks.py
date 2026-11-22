from celery import shared_task
import os
from pathlib import Path
from app.db.session import SessionLocal
from app.models.submission import Submission
from app.models.submission_chunk import SubmissionChunk
from app.models.processing_job import ProcessingJob
from app.services.ingestion import extract_text_from_file


@shared_task(bind=True, name="app.workers.tasks.process_submission_task", max_retries=3)
def process_submission_task(self, submission_id: str, local_file_path: str):
    """
    Celery background task to extract text chunks from a submission document
    and update extraction status idempotently.
    """
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return {"status": "error", "message": f"Submission {submission_id} not found"}
            
        # Idempotency check: if already completed, skip
        if submission.extraction_status == "completed":
            return {"status": "skipped", "message": "Already extracted"}

        submission.extraction_status = "processing"
        db.commit()

        file_path = Path(local_file_path)
        if not file_path.exists():
            submission.extraction_status = "failed"
            db.commit()
            return {"status": "error", "message": f"File not found at {local_file_path}"}

        # Extract text chunks
        chunks_data = extract_text_from_file(file_path)

        # Clear any existing chunks for idempotency on retry
        db.query(SubmissionChunk).filter(SubmissionChunk.submission_id == submission.id).delete()

        for c in chunks_data:
            chunk = SubmissionChunk(
                submission_id=submission.id,
                page=c["page"],
                paragraph=c["paragraph"],
                offset=c["offset"],
                original_text=c["original_text"],
                normalized_text=c["normalized_text"]
            )
            db.add(chunk)

        submission.extraction_status = "completed"
        db.commit()

        # Cleanup local temp file if inside temp dir
        try:
            if file_path.exists() and "plagix_temp" in str(file_path.resolve()):
                file_path.unlink()
        except Exception:
            pass

        return {"status": "completed", "submission_id": submission_id, "chunks_count": len(chunks_data)}

    except Exception as exc:
        db.rollback()
        try:
            sub = db.query(Submission).filter(Submission.id == submission_id).first()
            if sub:
                sub.extraction_status = "failed"
                db.commit()
        except Exception:
            pass
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    finally:
        db.close()
