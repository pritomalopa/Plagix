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


class GradeUpdateRequest(BaseModel):
    teacher_final_score: Optional[float] = Field(None, ge=0.0)
    override_reason: Optional[str] = Field(None, min_length=3, description="Mandatory reason for mark override")
    criterion_scores_override: Optional[Dict[str, Any]] = None
    teacher_feedback: Optional[str] = Field(None, description="Teacher comments or edited feedback")


class GradeFinalizeRequest(BaseModel):
    confirm_finalization: bool = Field(True, description="Confirmation to lock and finalize grade")


class GradeReopenRequest(BaseModel):
    reopen_reason: str = Field(..., min_length=3, description="Mandatory reason for reopening finalized grade")


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
    review_progress: Optional[Dict[str, Any]] = None
    batch_statistics: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    actor_id: Optional[UUID] = None
    action: str
    target_type: str
    target_id: UUID
    changes: Optional[Dict[str, Any]] = None
    created_at: datetime

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
    status_filter: Optional[str] = Query(None, description="Filter by status (pending, graded, reviewed, approved, finalized)"),
    quality_band: Optional[str] = Query(None, description="Filter by quality band"),
    min_score: Optional[float] = Query(None, description="Minimum score filter"),
    max_score: Optional[float] = Query(None, description="Maximum score filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve provisional and final grades for all submissions in an evaluation batch,
    including review progress statistics and filtering.
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
    status_counts = {"pending": 0, "graded": 0, "reviewed": 0, "approved": 0, "finalized": 0}

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
        st = r.status if r.status in status_counts else "graded"
        status_counts[st] = status_counts.get(st, 0) + 1

    stats = compute_batch_statistics(grade_dicts_for_stats)
    total_subs = len(submissions)
    reviewed_count = status_counts.get("reviewed", 0) + status_counts.get("approved", 0) + status_counts.get("finalized", 0)
    review_progress = {
        "total_submissions": total_subs,
        "graded_count": len(results),
        "reviewed_count": reviewed_count,
        "finalized_count": status_counts.get("finalized", 0),
        "percent_reviewed": round((reviewed_count / total_subs * 100), 1) if total_subs > 0 else 0.0,
        "status_breakdown": status_counts,
    }

    return {
        "grading_results": filtered_results,
        "total": len(filtered_results),
        "review_progress": review_progress,
        "batch_statistics": stats
    }


@router.get("/submissions/{submission_id}/grade", response_model=GradingResultResponse)
def get_submission_grade_detail(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed grading breakdown, AI suggestions, and teacher review state for a single submission.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    evaluation = db.query(Evaluation).filter(Evaluation.id == submission.evaluation_id).first()
    if not evaluation or evaluation.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

    grading = db.query(GradingResult).filter(GradingResult.submission_id == submission.id).first()
    if not grading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading result not found")

    return grading


@router.patch("/submissions/{submission_id}/grade", response_model=GradingResultResponse)
def update_submission_grade(
    submission_id: UUID,
    grade_in: GradeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Teacher review endpoint: update criterion-level marks, feedback, or override provisional scores.
    Prevents modifications if grade is finalized.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    evaluation = db.query(Evaluation).filter(Evaluation.id == submission.evaluation_id).first()
    if not evaluation or evaluation.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

    grading = db.query(GradingResult).filter(GradingResult.submission_id == submission.id).first()
    if not grading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading result not found")

    if grading.status == "finalized":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a finalized grade. Please reopen the grade first."
        )

    old_score = grading.teacher_final_score or grading.suggested_total
    changes_logged: Dict[str, Any] = {"old_score": old_score}

    existing_scores = grading.criterion_scores or {}
    if grade_in.criterion_scores_override:
        if isinstance(existing_scores, dict):
            existing_scores.update(grade_in.criterion_scores_override)
            grading.criterion_scores = existing_scores
        else:
            grading.criterion_scores = grade_in.criterion_scores_override
        changes_logged["criterion_scores_override"] = grade_in.criterion_scores_override

    if grade_in.teacher_feedback is not None:
        if isinstance(existing_scores, dict):
            existing_scores["teacher_feedback"] = grade_in.teacher_feedback
            grading.criterion_scores = existing_scores
        changes_logged["teacher_feedback"] = grade_in.teacher_feedback

    if grade_in.teacher_final_score is not None:
        grading.teacher_final_score = grade_in.teacher_final_score
        changes_logged["new_score"] = grade_in.teacher_final_score

    if grade_in.override_reason:
        grading.override_reason = grade_in.override_reason
        changes_logged["reason"] = grade_in.override_reason

    grading.status = "reviewed"
    db.commit()

    audit = AuditLog(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="update_grade_review",
        target_type="grading_result",
        target_id=grading.id,
        changes=changes_logged
    )
    db.add(audit)
    db.commit()
    db.refresh(grading)

    return grading


@router.post("/submissions/{submission_id}/finalize", response_model=GradingResultResponse)
def finalize_submission_grade(
    submission_id: UUID,
    finalize_in: GradeFinalizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lock and finalize a submission grade, preventing further edits without reopening.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    evaluation = db.query(Evaluation).filter(Evaluation.id == submission.evaluation_id).first()
    if not evaluation or evaluation.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

    grading = db.query(GradingResult).filter(GradingResult.submission_id == submission.id).first()
    if not grading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading result not found")

    grading.status = "finalized"
    grading.approved_at = datetime.now(timezone.utc)
    grading.approved_by = current_user.id
    db.commit()

    audit = AuditLog(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="finalize_grade",
        target_type="grading_result",
        target_id=grading.id,
        changes={"final_score": grading.teacher_final_score or grading.suggested_total}
    )
    db.add(audit)
    db.commit()
    db.refresh(grading)

    return grading


@router.post("/submissions/{submission_id}/reopen", response_model=GradingResultResponse)
def reopen_submission_grade(
    submission_id: UUID,
    reopen_in: GradeReopenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authorized mechanism to reopen a finalized grade with a mandatory reason.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    evaluation = db.query(Evaluation).filter(Evaluation.id == submission.evaluation_id).first()
    if not evaluation or evaluation.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

    grading = db.query(GradingResult).filter(GradingResult.submission_id == submission.id).first()
    if not grading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading result not found")

    if grading.status != "finalized":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Grade is not finalized.")

    grading.status = "reviewed"
    db.commit()

    audit = AuditLog(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="reopen_grade",
        target_type="grading_result",
        target_id=grading.id,
        changes={"reopen_reason": reopen_in.reopen_reason}
    )
    db.add(audit)
    db.commit()
    db.refresh(grading)

    return grading


@router.get("/{evaluation_id}/grading-audit", response_model=List[AuditLogResponse])
def get_evaluation_grading_audit(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve audit history for grading actions within an evaluation batch.
    Enforces tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    submissions = db.query(Submission).filter(Submission.evaluation_id == evaluation.id).all()
    sub_ids = [s.id for s in submissions]
    grading_ids = [g.id for g in db.query(GradingResult).filter(GradingResult.submission_id.in_(sub_ids)).all()]

    audit_logs = db.query(AuditLog).filter(
        AuditLog.tenant_id == current_user.tenant_id,
        AuditLog.target_type == "grading_result",
        AuditLog.target_id.in_(grading_ids) if grading_ids else False
    ).order_by(AuditLog.created_at.desc()).all()

    return audit_logs
