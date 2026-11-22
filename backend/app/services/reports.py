import csv
io_import = None
try:
    import io
except ImportError:
    pass

from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.grading_result import GradingResult
from app.models.relevance_result import RelevanceResult
from app.models.comparison import Comparison


def generate_gradebook_csv(evaluation: Evaluation, submissions: List[Submission], grading_results: List[GradingResult]) -> str:
    """
    Generate CSV gradebook export string containing student labels, filenames,
    suggested scores, final teacher scores, status, and quality bands.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Evaluation Title",
        "Student ID / Label",
        "Original Filename",
        "Suggested Total",
        "Teacher Final Score",
        "Grading Status",
        "Quality Band",
        "Review Flags",
        "Approved At"
    ])

    grading_by_sub = {g.submission_id: g for g in grading_results}

    for sub in submissions:
        g = grading_by_sub.get(sub.id)
        scores_dict = g.criterion_scores if g and isinstance(g.criterion_scores, dict) else {}
        band = scores_dict.get("quality_band", {}).get("label", "N/A")
        flags = ", ".join(scores_dict.get("review_flags", []))
        final_score = g.teacher_final_score if g and g.teacher_final_score is not None else (g.suggested_total if g else "N/A")
        suggested = g.suggested_total if g else "N/A"
        status = g.status if g else "pending"
        approved_at = str(g.approved_at) if g and g.approved_at else ""

        writer.writerow([
            evaluation.title,
            sub.student_label,
            sub.original_filename,
            suggested,
            final_score,
            status,
            band,
            flags,
            approved_at
        ])

    return output.getvalue()


def generate_evaluation_summary_report(
    evaluation: Evaluation,
    submissions: List[Submission],
    grading_results: List[GradingResult],
    relevance_results: List[RelevanceResult],
    comparisons: List[Comparison]
) -> Dict[str, Any]:
    """
    Generate comprehensive structured summary report for the evaluation batch.
    """
    grading_by_sub = {g.submission_id: g for g in grading_results}
    scores = [g.suggested_total for g in grading_results if g and g.suggested_total is not None]
    mean_score = sum(scores) / len(scores) if scores else 0.0

    sub_summaries = []
    for sub in submissions:
        g = grading_by_sub.get(sub.id)
        sub_summaries.append({
            "submission_id": str(sub.id),
            "student_label": sub.student_label,
            "filename": sub.original_filename,
            "suggested_total": g.suggested_total if g else None,
            "teacher_final_score": g.teacher_final_score if g else None,
            "status": g.status if g else "pending",
        })

    return {
        "evaluation_id": str(evaluation.id),
        "title": evaluation.title,
        "max_marks": evaluation.max_marks,
        "total_submissions": len(submissions),
        "total_graded": len(grading_results),
        "mean_score": round(mean_score, 2),
        "submissions": sub_summaries,
        "total_comparisons": len(comparisons),
        "plagiarism_flags_count": sum(1 for c in comparisons if (c.exact_score or 0) > 0.7 or (c.lexical_score or 0) > 0.7),
    }
