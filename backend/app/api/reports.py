from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID

from app.db.session import get_db
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.grading_result import GradingResult
from app.models.relevance_result import RelevanceResult
from app.models.comparison import Comparison
from app.api.deps import get_current_user, verify_evaluation_ownership
from app.services.reports import generate_gradebook_csv, generate_evaluation_summary_report

router = APIRouter(prefix="/evaluations", tags=["Reports & Export"])


@router.get("/{evaluation_id}/reports/csv")
def export_gradebook_csv(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export gradebook as a downloadable CSV file for spreadsheet integration.
    Enforces strict tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    submissions = db.query(Submission).filter(Submission.evaluation_id == evaluation.id).all()
    sub_ids = [s.id for s in submissions]
    grading_results = db.query(GradingResult).filter(GradingResult.submission_id.in_(sub_ids)).all() if sub_ids else []

    csv_content = generate_gradebook_csv(evaluation, submissions, grading_results)

    filename = f"plagix_grades_{evaluation.title.lower().replace(' ', '_')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{evaluation_id}/reports/summary")
def get_evaluation_summary_json(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve comprehensive evaluation summary report data (JSON format).
    Enforces strict tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)

    submissions = db.query(Submission).filter(Submission.evaluation_id == evaluation.id).all()
    sub_ids = [s.id for s in submissions]
    grading_results = db.query(GradingResult).filter(GradingResult.submission_id.in_(sub_ids)).all() if sub_ids else []
    relevance_results = db.query(RelevanceResult).filter(RelevanceResult.submission_id.in_(sub_ids)).all() if sub_ids else []
    comparisons = db.query(Comparison).filter(Comparison.evaluation_id == evaluation.id).all()

    report_data = generate_evaluation_summary_report(
        evaluation, submissions, grading_results, relevance_results, comparisons
    )

    return report_data
