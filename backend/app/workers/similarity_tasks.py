from celery import shared_task
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.submission_chunk import SubmissionChunk
from app.models.comparison import Comparison
from app.models.matched_passage import MatchedPassage
from app.services.similarity import (
    calculate_exact_similarity,
    calculate_lexical_similarity,
    calculate_semantic_similarity,
    filter_common_content
)


@shared_task(bind=True, name="app.workers.similarity_tasks.run_evaluation_comparison_task", max_retries=3)
def run_evaluation_comparison_task(self, evaluation_id: str):
    """
    Asynchronous Celery task to perform N * (N - 1) / 2 canonical pairwise comparisons
    for all accepted submissions within a given evaluation.
    """
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        eval_uuid = UUID(evaluation_id) if isinstance(evaluation_id, str) else evaluation_id
        evaluation = db.query(Evaluation).filter(Evaluation.id == eval_uuid).first()
        if not evaluation:
            print(f"DEBUG: Evaluation {evaluation_id} not found in DB")
            return {"status": "error", "message": f"Evaluation {evaluation_id} not found"}

        # Fetch all completed submissions for this evaluation
        submissions = db.query(Submission).filter(
            Submission.evaluation_id == eval_uuid,
            Submission.extraction_status == "completed"
        ).all()
        print(f"DEBUG: Found {len(submissions)} completed submissions for eval {eval_uuid}")

        n = len(submissions)
        if n < 2:
            evaluation.status = "completed"
            db.commit()
            return {"status": "completed", "message": "Fewer than 2 submissions; no pairs to compare."}

        # Get question prompt for common content filtering
        question_prompt = ""
        if evaluation.questions:
            question_prompt = evaluation.questions[0].prompt

        evaluation.status = "comparing"
        db.commit()

        pairs_compared = 0

        for i in range(n):
            for j in range(i + 1, n):
                sub_a = submissions[i]
                sub_b = submissions[j]

                # Enforce canonical ordering: sub_a_id < sub_b_id
                if sub_a.id > sub_b.id:
                    sub_a, sub_b = sub_b, sub_a

                # Idempotency check: does comparison already exist?
                existing_comp = db.query(Comparison).filter(
                    Comparison.evaluation_id == eval_uuid,
                    Comparison.submission_a_id == sub_a.id,
                    Comparison.submission_b_id == sub_b.id
                ).first()

                if existing_comp and existing_comp.status == "completed":
                    continue

                # Fetch text chunks
                chunks_a = db.query(SubmissionChunk).filter(SubmissionChunk.submission_id == sub_a.id).all()
                chunks_b = db.query(SubmissionChunk).filter(SubmissionChunk.submission_id == sub_b.id).all()

                text_a = " ".join(c.original_text for c in chunks_a)
                text_b = " ".join(c.original_text for c in chunks_b)

                # Filter boilerplate
                filtered_a = filter_common_content(text_a, question_prompt)
                filtered_b = filter_common_content(text_b, question_prompt)

                # Calculate dimensions
                exact_score, exact_passages = calculate_exact_similarity(filtered_a, filtered_b)
                lexical_score, _ = calculate_lexical_similarity(filtered_a, filtered_b)
                semantic_score, _ = calculate_semantic_similarity(filtered_a, filtered_b)

                if existing_comp:
                    comp = existing_comp
                    comp.exact_score = exact_score
                    comp.lexical_score = lexical_score
                    comp.semantic_score = semantic_score
                    comp.status = "completed"
                    # Clear old passages
                    db.query(MatchedPassage).filter(MatchedPassage.comparison_id == comp.id).delete()
                else:
                    comp = Comparison(
                        evaluation_id=eval_uuid,
                        submission_a_id=sub_a.id,
                        submission_b_id=sub_b.id,
                        exact_score=exact_score,
                        lexical_score=lexical_score,
                        semantic_score=semantic_score,
                        status="completed",
                        metadata_={"algorithm": "winnowing_tfidf_embeddings"}
                    )
                    db.add(comp)
                    db.flush()

                # Save matched passages evidence
                for p in exact_passages:
                    passage = MatchedPassage(
                        comparison_id=comp.id,
                        text_a_excerpt=p["text_a_excerpt"][:200],
                        text_b_excerpt=p["text_b_excerpt"][:200],
                        match_type=p["match_type"],
                        similarity=p["similarity"]
                    )
                    db.add(passage)

                pairs_compared += 1
                db.commit()

        evaluation.status = "ready_for_review"
        db.commit()

        return {
            "status": "completed",
            "evaluation_id": evaluation_id,
            "pairs_compared": pairs_compared
        }

    except Exception as exc:
        db.rollback()
        try:
            eval_obj = db.query(Evaluation).filter(Evaluation.id == UUID(evaluation_id)).first()
            if eval_obj:
                eval_obj.status = "failed"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    finally:
        db.close()
