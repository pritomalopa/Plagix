from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.relevance_result import RelevanceResult
from app.api.deps import get_current_user, verify_evaluation_ownership
from app.workers.relevance_tasks import run_evaluation_relevance_task

router = APIRouter(prefix="/evaluations", tags=["Answer Relevance & Concept Analysis"])


@router.post("/{evaluation_id}/relevance", status_code=status.HTTP_202_ACCEPTED)
def start_relevance_analysis(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start asynchronous answer relevance and concept coverage analysis for all submissions
    in an evaluation batch. Enforces strict tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    # Dispatch Celery background task
    run_evaluation_relevance_task.delay(str(evaluation.id))

    return {
        "status": "queued",
        "evaluation_id": evaluation.id,
        "message": "Answer relevance analysis started in background."
    }


@router.get("/{evaluation_id}/relevance", status_code=status.HTTP_200_OK)
def get_evaluation_relevance_results(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve answer relevance and concept coverage results for all submissions in an evaluation batch.
    Enforces strict tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    submissions = db.query(Submission).filter(Submission.evaluation_id == evaluation.id).all()
    sub_ids = [s.id for s in submissions]

    results = db.query(RelevanceResult).filter(RelevanceResult.submission_id.in_(sub_ids)).all()

    sub_lookup = {s.id: s for s in submissions}
    response_items = []

    for r in results:
        sub = sub_lookup.get(r.submission_id)
        response_items.append({
            "id": r.id,
            "submission_id": r.submission_id,
            "student_label": sub.student_label if sub else "Unknown",
            "filename": sub.original_filename if sub else "Unknown",
            "category": r.category,
            "score": r.score,
            "confidence": r.confidence,
            "rationale": r.rationale,
            "evidence": r.evidence,
            "model_version": r.model_version
        })

    return {
        "relevance_results": response_items,
        "total": len(response_items)
    }
