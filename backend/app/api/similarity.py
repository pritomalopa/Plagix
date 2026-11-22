from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.comparison import Comparison
from app.models.matched_passage import MatchedPassage
from app.api.deps import get_current_user, verify_evaluation_ownership
from app.workers.similarity_tasks import run_evaluation_comparison_task

router = APIRouter(prefix="/evaluations", tags=["Plagiarism Similarity Analysis"])


@router.post("/{evaluation_id}/compare", status_code=status.HTTP_202_ACCEPTED)
def start_comparison(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start asynchronous pairwise similarity analysis for all submissions in an evaluation batch.
    Enforces strict tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    # Dispatch Celery background task
    run_evaluation_comparison_task.delay(str(evaluation.id))

    return {
        "status": "queued",
        "evaluation_id": evaluation.id,
        "message": "Pairwise comparison analysis started in background."
    }


@router.get("/{evaluation_id}/comparisons", status_code=status.HTTP_200_OK)
def list_comparisons(
    evaluation_id: UUID,
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve ranked similarity comparisons for an evaluation batch, filtered by minimum score.
    Enforces strict tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    comparisons = db.query(Comparison).filter(
        Comparison.evaluation_id == evaluation.id,
        (Comparison.lexical_score >= min_score) | (Comparison.semantic_score >= min_score)
    ).order_by(Comparison.lexical_score.desc()).all()

    results = []
    for c in comparisons:
        sub_a = db.get(Submission, c.submission_a_id)
        sub_b = db.get(Submission, c.submission_b_id)
        results.append({
            "id": c.id,
            "evaluation_id": c.evaluation_id,
            "submission_a": {
                "id": sub_a.id if sub_a else None,
                "student_label": sub_a.student_label if sub_a else "Unknown",
                "filename": sub_a.original_filename if sub_a else "Unknown"
            },
            "submission_b": {
                "id": sub_b.id if sub_b else None,
                "student_label": sub_b.student_label if sub_b else "Unknown",
                "filename": sub_b.original_filename if sub_b else "Unknown"
            },
            "exact_score": c.exact_score,
            "lexical_score": c.lexical_score,
            "semantic_score": c.semantic_score,
            "status": c.status
        })

    return {
        "comparisons": results,
        "total": len(results)
    }


@router.get("/{evaluation_id}/comparisons/{comparison_id}/passages", status_code=status.HTTP_200_OK)
def get_matched_passages(
    evaluation_id: UUID,
    comparison_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve explainable matching passage evidence for a specific pairwise comparison.
    Enforces strict tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    comparison = db.query(Comparison).filter(
        Comparison.id == comparison_id,
        Comparison.evaluation_id == evaluation.id
    ).first()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found"
        )

    passages = db.query(MatchedPassage).filter(MatchedPassage.comparison_id == comparison.id).all()

    return {
        "comparison_id": comparison.id,
        "submission_a_id": comparison.submission_a_id,
        "submission_b_id": comparison.submission_b_id,
        "exact_score": comparison.exact_score,
        "lexical_score": comparison.lexical_score,
        "semantic_score": comparison.semantic_score,
        "matched_passages": [
            {
                "id": p.id,
                "match_type": p.match_type,
                "similarity": p.similarity,
                "text_a_excerpt": p.text_a_excerpt,
                "text_b_excerpt": p.text_b_excerpt
            }
            for p in passages
        ],
        "warning": "Similarity is a review signal for human evaluation, not definitive proof of academic misconduct."
    }
