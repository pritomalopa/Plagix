from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID, uuid4
from pathlib import Path
import tempfile
import shutil

from app.db.session import get_db
from app.models.user import User
from app.models.submission import Submission
from app.api.evaluations import verify_evaluation_ownership
from app.api.deps import get_current_user, verify_evaluation_ownership
from app.services.ingestion import (
    validate_file_extension,
    compute_file_hash,
    derive_student_label,
    safe_extract_zip,
    MAX_INDIVIDUAL_FILE_SIZE,
    MAX_FILE_COUNT
)
from app.schemas.submission import SubmissionResponse, SubmissionListResponse
from app.workers.ingestion_tasks import process_submission_task

router = APIRouter(prefix="/evaluations", tags=["Submissions Ingestion"])


@router.post("/{evaluation_id}/upload", response_model=SubmissionListResponse, status_code=status.HTTP_201_CREATED)
def upload_submissions(
    evaluation_id: UUID,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload individual files (PDF, DOCX, TXT) and/or ZIP archives to an evaluation batch.
    Validates file extensions, size limits, extracts ZIP securely, checks for SHA-256 duplicates,
    creates submission records, and dispatches background text extraction tasks via Celery.
    Enforces strict tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for upload."
        )

    accepted_submissions = []
    temp_dir = Path(tempfile.mkdtemp(prefix="plagix_upload_"))

    try:
        all_files_to_process = []

        for upload_file in files:
            filename = upload_file.filename or "unknown"
            ext = validate_file_extension(filename)
            
            # Read file bytes into memory
            file_bytes = upload_file.file.read()
            if len(file_bytes) > MAX_INDIVIDUAL_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File '{filename}' exceeds 50 MB size limit."
                )

            if ext == ".zip":
                # Save ZIP temporarily and safely extract
                zip_temp = temp_dir / f"{uuid4()}_{filename}"
                with open(zip_temp, "wb") as f:
                    f.write(file_bytes)
                    
                extracted_paths = safe_extract_zip(zip_temp, temp_dir)
                for p in extracted_paths:
                    all_files_to_process.append((p.name, p))
            else:
                doc_temp = temp_dir / f"{uuid4()}_{filename}"
                with open(doc_temp, "wb") as f:
                    f.write(file_bytes)
                all_files_to_process.append((filename, doc_temp))

        if len(all_files_to_process) > MAX_FILE_COUNT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total file count ({len(all_files_to_process)}) exceeds maximum limit of {MAX_FILE_COUNT}."
            )

        # Process each valid document
        for orig_name, file_path in all_files_to_process:
            with open(file_path, "rb") as f:
                content_bytes = f.read()

            file_hash = compute_file_hash(content_bytes)

            # Check duplicate within this evaluation
            existing = db.query(Submission).filter(
                Submission.evaluation_id == evaluation.id,
                Submission.file_hash == file_hash
            ).first()

            if existing:
                # Skip duplicate
                continue

            student_label, _ = derive_student_label(orig_name)
            storage_key = f"tenants/{evaluation.tenant_id}/evaluations/{evaluation.id}/submissions/{uuid4()}_{orig_name}"

            submission = Submission(
                evaluation_id=evaluation.id,
                student_label=student_label,
                original_filename=orig_name,
                file_hash=file_hash,
                storage_key=storage_key,
                extraction_status="pending",
                metadata_={"size_bytes": len(content_bytes)}
            )
            db.add(submission)
            db.flush()

            # Save file permanently to storage directory
            storage_dir = Path("storage") / str(evaluation.tenant_id) / str(evaluation.id)
            storage_dir.mkdir(parents=True, exist_ok=True)
            saved_file_path = storage_dir / f"{submission.id}_{orig_name}"
            shutil.copyfile(file_path, saved_file_path)

            accepted_submissions.append(submission)

            # Dispatch Celery background task for text extraction
            process_submission_task.delay(str(submission.id), str(saved_file_path.resolve()))

        db.commit()
        for sub in accepted_submissions:
            db.refresh(sub)

        return {
            "submissions": accepted_submissions,
            "total": len(accepted_submissions)
        }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/{evaluation_id}/submissions", response_model=SubmissionListResponse)
def list_submissions(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all submissions for an evaluation batch. Enforces tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)
    submissions = db.query(Submission).filter(Submission.evaluation_id == evaluation.id).all()
    return {
        "submissions": submissions,
        "total": len(submissions)
    }


@router.get("/{evaluation_id}/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    evaluation_id: UUID,
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve single submission detail. Enforces tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.evaluation_id == evaluation.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    return submission
