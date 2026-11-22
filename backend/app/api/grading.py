from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.grading_result import GradingResult
from app.models.audit_logs import AuditLog
from app.api.deps import get_current_user, verify_evaluation_ownership
from app.workers.grading_tasks import run_evaluation_grading_task
from app.services.grading import compute_batch_statistics

router = APIRouter(prefix="/evaluations", tags=["Rubric Grading & Teacher Review"])


class GradeOverrideRequest(BaseModel):
    teacher_final_score: float = Field(..., ge=0.0)
    override_reason: str = Field(..., min_length=3, description="Mandatory reason for mark override")
    criterion_scores_override: Optional[Dict[str, Any]] = None


class GradingResultResponse(BaseModel):
    id: UUID
    submission_id: UUID
    criterion_scores: Dict[str, Any]
    suggested_total: float
    confidence: Optional[float] = None
    teacher_final_score: Optional[float] = None
    status: str
    override_reason: Optional[str] = None
    suggested_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class GradingBatchResponse(BaseModel):
    grading_results: List[GradingResultResponse]
    total: int
    batch_statistics: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


@router.post("/{evaluation_id}/grade", status_code=status.HTTP_202_ACCEPTED)
def start_grading_analysis(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start asynchronous rubric-based provisional grading for all submissions in an evaluation batch.
    Enforces strict tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    run_evaluation_grading_task.delay(str(evaluation.id))

    return {
        "status": "queued",
        "evaluation_id": evaluation.id,
        "message": "Provisional rubric grading analysis started in background."
    }


@router.get("/{evaluation_id}/grading-results", response_model=GradingBatchResponse)
def get_evaluation_grading_results(
    evaluation_id: UUID,
    status_filter: Optional[str] = Query(None, description="Filter by status (graded, approved, pending)"),
    quality_band: Optional[str] = Query(None, description="Filter by quality band (excellent, good, etc.)"),
    min_score: Optional[float] = Query(None, description="Minimum score filter"),
    max_score: Optional[float] = Query(None, description="Maximum score filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve provisional and final grades for all submissions in an evaluation batch,
    with optional filtering by status, quality band, and score range, plus batch statistics.
    Enforces strict tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    submissions = db.query(Submission).filter(Submission.evaluation_id == evaluation.id).all()
    sub_ids = [s.id for s in submissions]

    query = db.query(GradingResult).filter(GradingResult.submission_id.in_(sub_ids))
    if status_filter:
        query = query.filter(GradingResult.status == status_filter)
    if min_score is not None:
        query = query.filter(GradingResult.suggested_total >= min_score)
    if max_score is not None:
        query = query.filter(GradingResult.suggested_total <= max_score)

    results = query.all()

    filtered_results = []
    grade_dicts_for_stats = []
    for r in results:
        scores_dict = r.criterion_scores or {}
        band_info = scores_dict.get("quality_band", {})
        if quality_band and band_info.get("band") != quality_band:
            continue
        filtered_results.append(r)
        grade_dicts_for_stats.append({
            "suggested_total": r.suggested_total,
            "quality_band": band_info,
            "review_flags": scores_dict.get("review_flags", []),
        })

    stats = compute_batch_statistics(grade_dicts_for_stats)

    return {
        "grading_results": filtered_results,
        "total": len(filtered_results),
        "batch_statistics": stats
    }


@router.get("/submissions/{submission_id}/grade", response_model=GradingResultResponse)
def get_submission_grade_detail(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed grading breakdown for a single submission.
    Enforces strict tenant isolation.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    evaluation = db.query(Evaluation).filter(Evaluation.id == submission.evaluation_id).first()
    if not evaluation or evaluation.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: submission belongs to another tenant"
        )

    grading = db.query(GradingResult).filter(GradingResult.submission_id == submission.id).first()
    if not grading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grading result not found for this submission"
        )

    return grading


@router.patch("/submissions/{submission_id}/grade", response_model=GradingResultResponse)
def override_submission_grade(
    submission_id: UUID,
    grade_in: GradeOverrideRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Teacher override endpoint: edit provisional marks, provide mandatory reason,
    approve final grade, and record an immutable audit log entry.
    Enforces tenant isolation.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    evaluation = db.query(Evaluation).filter(Evaluation.id == submission.evaluation_id).first()
    if not evaluation or evaluation.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: submission belongs to another tenant"
        )

    grading = db.query(GradingResult).filter(GradingResult.submission_id == submission.id).first()
    if not grading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grading result not found for this submission"
        )

    old_score = grading.teacher_final_score or grading.suggested_total

    if grade_in.criterion_scores_override:
        existing_scores = grading.criterion_scores or {}
        if isinstance(existing_scores, dict):
            existing_scores.update(grade_in.criterion_scores_override)
            grading.criterion_scores = existing_scores
        else:
            grading.criterion_scores = grade_in.criterion_scores_override

    grading.teacher_final_score = grade_in.teacher_final_score
    grading.override_reason = grade_in.override_reason
    grading.status = "approved"
    grading.approved_at = datetime.now(timezone.utc)
    grading.approved_by = current_user.id

    db.commit()

    audit = AuditLog(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="override_grade",
        target_type="grading_result",
        target_id=grading.id,
        changes={
            "old_score": old_score,
            "new_score": grade_in.teacher_final_score,
            "reason": grade_in.override_reason
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(grading)

    return grading
