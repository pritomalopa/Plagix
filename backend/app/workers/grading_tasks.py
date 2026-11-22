from celery import shared_task
from uuid import UUID
from datetime import datetime, timezone
from app.services.grading import (
    calculate_submission_grades,
    get_submission_similarity_data,
    compute_batch_statistics,
)


@shared_task(bind=True, name="app.workers.grading_tasks.run_evaluation_grading_task", max_retries=3)
def run_evaluation_grading_task(self, evaluation_id: str):
    from app.db.session import SessionLocal
    from app.models.evaluation import Evaluation
    from app.models.submission import Submission
    from app.models.submission_chunk import SubmissionChunk
    from app.models.relevance_result import RelevanceResult
    from app.models.grading_result import GradingResult

    db = SessionLocal()
    try:
        eval_uuid = UUID(evaluation_id) if isinstance(evaluation_id, str) else evaluation_id
        evaluation = db.query(Evaluation).filter(Evaluation.id == eval_uuid).first()
        if not evaluation:
            return {"status": "error", "message": f"Evaluation {evaluation_id} not found"}

        if not evaluation.questions:
            return {"status": "completed", "message": "No questions defined for evaluation."}

        review_thresholds = None
        if evaluation.settings and isinstance(evaluation.settings, dict):
            review_thresholds = evaluation.settings.get("review_thresholds")

        submissions = db.query(Submission).filter(
            Submission.evaluation_id == eval_uuid,
            Submission.extraction_status == "completed"
        ).all()

        graded_count = 0
        grade_summaries = []

        for sub in submissions:
            chunks = db.query(SubmissionChunk).filter(
                SubmissionChunk.submission_id == sub.id
            ).all()

            relevance_results = db.query(RelevanceResult).filter(
                RelevanceResult.submission_id == sub.id
            ).all()

            similarity_data = get_submission_similarity_data(db, sub.id, eval_uuid)

            grade_data = calculate_submission_grades(
                evaluation, sub, chunks, relevance_results,
                similarity_data=similarity_data,
                review_thresholds=review_thresholds,
            )

            existing = db.query(GradingResult).filter(
                GradingResult.submission_id == sub.id
            ).first()

            criterion_payload = {
                "question_grades": grade_data["question_grades"],
                "feedback": grade_data["feedback"],
                "quality_band": grade_data["quality_band"],
                "review_flags": grade_data["review_flags"],
                "max_possible": grade_data.get("max_possible"),
                "similarity_data": similarity_data,
            }

            if existing:
                if existing.status == "approved":
                    continue
                existing.criterion_scores = criterion_payload
                existing.suggested_total = grade_data["suggested_total"]
                existing.confidence = grade_data["confidence"]
                existing.suggested_at = datetime.now(timezone.utc)
                existing.status = "graded"
            else:
                grading = GradingResult(
                    submission_id=sub.id,
                    criterion_scores=criterion_payload,
                    suggested_total=grade_data["suggested_total"],
                    confidence=grade_data["confidence"],
                    status="graded",
                    suggested_at=datetime.now(timezone.utc),
                )
                db.add(grading)

            grade_summaries.append(grade_data)
            graded_count += 1
            db.commit()

        stats = compute_batch_statistics(grade_summaries) if grade_summaries else {}

        return {
            "status": "completed",
            "evaluation_id": evaluation_id,
            "graded_submissions": graded_count,
            "batch_statistics": stats,
        }

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    finally:
        db.close()
