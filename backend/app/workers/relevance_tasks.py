from celery import shared_task
from uuid import UUID


@shared_task(bind=True, name="app.workers.relevance_tasks.run_evaluation_relevance_task", max_retries=3)
def run_evaluation_relevance_task(self, evaluation_id: str):
    """
    Asynchronous Celery task to evaluate answer relevance and concept coverage
    for all completed submissions in an evaluation batch.
    """
    from app.db.session import SessionLocal
    from app.models.evaluation import Evaluation
    from app.models.submission import Submission
    from app.models.submission_chunk import SubmissionChunk
    from app.models.relevance_result import RelevanceResult
    from app.services.relevance import analyze_answer_relevance

    db = SessionLocal()
    try:
        eval_uuid = UUID(evaluation_id) if isinstance(evaluation_id, str) else evaluation_id
        evaluation = db.query(Evaluation).filter(Evaluation.id == eval_uuid).first()
        if not evaluation:
            return {"status": "error", "message": f"Evaluation {evaluation_id} not found"}

        if not evaluation.questions:
            return {"status": "completed", "message": "No questions defined for evaluation."}

        primary_question = evaluation.questions[0]

        submissions = db.query(Submission).filter(
            Submission.evaluation_id == eval_uuid,
            Submission.extraction_status == "completed"
        ).all()

        analyzed_count = 0

        for sub in submissions:
            chunks = db.query(SubmissionChunk).filter(SubmissionChunk.submission_id == sub.id).all()
            
            result_data = analyze_answer_relevance(primary_question, sub, chunks)

            # Check if relevance result already exists (idempotency)
            existing = db.query(RelevanceResult).filter(
                RelevanceResult.submission_id == sub.id,
                RelevanceResult.question_id == primary_question.id
            ).first()

            if existing:
                existing.category = result_data["category"]
                existing.score = result_data["score"]
                existing.confidence = result_data["confidence"]
                existing.rationale = result_data["rationale"]
                existing.evidence = {
                    "excerpts": result_data["evidence"],
                    "concepts_coverage": result_data["concepts_coverage"]
                }
                existing.model_version = result_data["model_version"]
            else:
                rel = RelevanceResult(
                    submission_id=sub.id,
                    question_id=primary_question.id,
                    category=result_data["category"],
                    score=result_data["score"],
                    confidence=result_data["confidence"],
                    rationale=result_data["rationale"],
                    evidence={
                        "excerpts": result_data["evidence"],
                        "concepts_coverage": result_data["concepts_coverage"]
                    },
                    model_version=result_data["model_version"]
                )
                db.add(rel)

            analyzed_count += 1
            db.commit()

        return {
            "status": "completed",
            "evaluation_id": evaluation_id,
            "analyzed_submissions": analyzed_count
        }

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    finally:
        db.close()
