from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.evaluation import Evaluation
from app.models.question import Question
from app.models.rubric_criterion import RubricCriterion
from app.models.submission import Submission
from app.models.submission_chunk import SubmissionChunk
from app.models.relevance_result import RelevanceResult
from app.models.comparison import Comparison
from app.services.similarity import get_embedding_model, DEFAULT_EMBEDDING_MODEL
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

QUALITY_BANDS = [
    {"band": "excellent", "min": 0.85, "label": "Excellent"},
    {"band": "good", "min": 0.70, "label": "Good"},
    {"band": "satisfactory", "min": 0.50, "label": "Satisfactory"},
    {"band": "needs_improvement", "min": 0.30, "label": "Needs Improvement"},
    {"band": "poor", "min": 0.0, "label": "Poor"},
]

DEFAULT_REVIEW_THRESHOLDS = {
    "low_confidence": 0.45,
    "high_similarity_flag": 0.70,
    "auto_flag_off_topic": True,
}


def classify_quality_band(score_ratio: float) -> Dict[str, str]:
    for band in QUALITY_BANDS:
        if score_ratio >= band["min"]:
            return {"band": band["band"], "label": band["label"]}
    return {"band": "poor", "label": "Poor"}


def _calculate_reference_answer_bonus(
    reference_answer: Optional[str],
    answer_text: str,
    model: Any,
) -> float:
    if not reference_answer or not reference_answer.strip() or not answer_text.strip():
        return 0.0
    if model is None:
        ref_words = set(reference_answer.lower().split())
        ans_words = set(answer_text.lower().split())
        return len(ref_words.intersection(ans_words)) / max(len(ref_words), 1)
    try:
        embeddings = model.encode([reference_answer, answer_text], convert_to_numpy=True)
        score = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
        return max(0.0, min(1.0, score))
    except Exception as e:
        logger.error("Error computing reference answer alignment: %s", e)
        return 0.0


def _score_criterion(
    criterion: RubricCriterion,
    answer_text: str,
    model: Any,
    relevance: Optional[RelevanceResult],
    concepts_coverage: List[Dict],
    reference_score: float,
) -> Dict[str, Any]:
    criterion_text = f"{criterion.criterion} {criterion.description or ''} {criterion.expected_evidence or ''}"

    base_score = 0.5
    if model is not None and answer_text.strip():
        try:
            c_emb = model.encode([criterion_text], convert_to_numpy=True)
            a_emb = model.encode([answer_text], convert_to_numpy=True)
            base_score = float(cosine_similarity(c_emb, a_emb)[0][0])
            base_score = max(0.0, min(1.0, base_score))
        except Exception as e:
            logger.error("Error calculating criterion embedding match: %s", e)
    elif answer_text.strip():
        keywords = set(criterion_text.lower().split())
        ans_words = set(answer_text.lower().split())
        base_score = len(keywords.intersection(ans_words)) / max(len(keywords), 1)

    coverage_boost = 0.0
    matched_concepts = []
    if criterion.expected_evidence and concepts_coverage:
        evidence_keywords = set(criterion.expected_evidence.lower().split())
        for cc in concepts_coverage:
            concept_words = set(cc["concept"].lower().split())
            if concept_words.intersection(evidence_keywords):
                if cc["status"] == "present":
                    coverage_boost += 0.05
                    matched_concepts.append(cc["concept"])
                elif cc["status"] == "partially_covered":
                    coverage_boost += 0.02

    if reference_score > 0.0:
        ref_weight = 0.15
        composite_score = base_score * (1.0 - ref_weight) + reference_score * ref_weight + coverage_boost
    else:
        composite_score = base_score + coverage_boost

    if relevance:
        if relevance.category == "relevant":
            composite_score = max(composite_score, 0.80)
        elif relevance.category == "partially_relevant":
            composite_score = min(composite_score, 0.65)
        elif relevance.category == "off_topic":
            composite_score = min(composite_score, 0.15)

    composite_score = max(0.0, min(1.0, composite_score))

    awarded_points = round(composite_score * criterion.max_points, 1)
    awarded_points = min(float(criterion.max_points), max(0.0, awarded_points))

    strengths = []
    missing = []
    suggestions = []

    if composite_score >= 0.7:
        strengths.append(f"Demonstrates strong understanding of '{criterion.criterion}'.")
        if matched_concepts:
            strengths.append(f"Key concepts addressed: {', '.join(matched_concepts)}.")
    elif composite_score >= 0.4:
        strengths.append(f"Touches upon aspects of '{criterion.criterion}'.")
        missing.append(f"Needs deeper explanation or supporting evidence for '{criterion.criterion}'.")
        suggestions.append(f"Consider elaborating on key points related to '{criterion.criterion}'.")
    else:
        missing.append(f"Did not demonstrate expected understanding for '{criterion.criterion}'.")
        if criterion.expected_evidence:
            suggestions.append(f"Review expected evidence: {criterion.expected_evidence[:150]}.")

    return {
        "name": criterion.criterion,
        "max_points": criterion.max_points,
        "awarded_points": awarded_points,
        "weight": criterion.weight,
        "semantic_alignment": round(base_score, 4),
        "reference_alignment": round(reference_score, 4) if reference_score > 0 else None,
        "composite_score": round(composite_score, 4),
        "justification": f"Evaluated with composite alignment score of {composite_score:.1%} (semantic: {base_score:.1%}).",
        "strengths": strengths,
        "missing_elements": missing,
        "suggestions": suggestions,
        "matched_concepts": matched_concepts,
        "confidence": composite_score,
    }


def calculate_provisional_grades(
    evaluation: Evaluation,
    question: Question,
    submission: Submission,
    chunks: List[SubmissionChunk],
    relevance: Optional[RelevanceResult],
    similarity_data: Optional[Dict[str, Any]] = None,
    review_thresholds: Optional[Dict[str, Any]] = None,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> Dict[str, Any]:
    thresholds = {**DEFAULT_REVIEW_THRESHOLDS, **(review_thresholds or {})}
    answer_text = " ".join(c.original_text for c in chunks)
    criteria = question.rubric_criteria or []

    if not criteria:
        rel_score = relevance.score if relevance else 0.5
        suggested_total = round(rel_score * evaluation.max_marks, 2)
        band = classify_quality_band(rel_score)
        return {
            "criterion_scores": {
                "overall": {
                    "name": "Overall Relevance & Alignment",
                    "max_points": evaluation.max_marks,
                    "awarded_points": suggested_total,
                    "justification": "Provisional mark estimated from answer relevance (no rubric configured).",
                    "strengths": ["Answer submitted and analyzed."],
                    "missing_elements": ["Specific rubric criteria were not provided by teacher."],
                    "suggestions": ["Configure a detailed rubric for granular scoring."],
                    "confidence": relevance.confidence if relevance else 0.5,
                }
            },
            "suggested_total": suggested_total,
            "confidence": relevance.confidence if relevance else 0.5,
            "quality_band": band,
            "feedback": "Provisional grade generated based on question relevance. Please configure a rubric for granular scoring.",
            "review_flags": ["no_rubric"],
        }

    model = get_embedding_model(model_name)

    concepts_coverage = []
    if relevance and relevance.evidence and isinstance(relevance.evidence, dict):
        concepts_coverage = relevance.evidence.get("concepts_coverage", [])

    reference_score = _calculate_reference_answer_bonus(
        question.reference_answer, answer_text, model
    )

    criterion_scores = {}
    total_weighted_awarded = 0.0
    total_weighted_max = 0.0
    confidences = []

    for c in criteria:
        result = _score_criterion(c, answer_text, model, relevance, concepts_coverage, reference_score)
        criterion_scores[str(c.id)] = result

        weighted_awarded = result["awarded_points"] * c.weight
        weighted_max = c.max_points * c.weight
        total_weighted_awarded += weighted_awarded
        total_weighted_max += weighted_max
        confidences.append(result["confidence"])

    if total_weighted_max > 0:
        score_ratio = total_weighted_awarded / total_weighted_max
        raw_total = sum(r["awarded_points"] for r in criterion_scores.values())
    else:
        score_ratio = 0.0
        raw_total = 0.0

    suggested_total = round(raw_total, 2)
    overall_confidence = sum(confidences) / len(confidences) if confidences else 0.5
    band = classify_quality_band(score_ratio)

    review_flags = []
    if overall_confidence < thresholds["low_confidence"]:
        review_flags.append("low_confidence")
    if relevance and relevance.category == "off_topic" and thresholds.get("auto_flag_off_topic"):
        review_flags.append("off_topic_submission")

    if similarity_data:
        max_sim = similarity_data.get("max_similarity", 0.0)
        if max_sim >= thresholds["high_similarity_flag"]:
            review_flags.append("high_similarity")

    feedback_parts = []
    total_max = sum(c.max_points for c in criteria)
    feedback_parts.append(f"Provisional Score: {suggested_total} / {total_max} ({band['label']}).")
    for cid, cdata in criterion_scores.items():
        if cdata["strengths"]:
            feedback_parts.append(f"Strength in {cdata['name']}: {cdata['strengths'][0]}")
        if cdata["missing_elements"]:
            feedback_parts.append(f"Improvement needed in {cdata['name']}: {cdata['missing_elements'][0]}")
        if cdata["suggestions"]:
            feedback_parts.append(f"Suggestion for {cdata['name']}: {cdata['suggestions'][0]}")

    return {
        "criterion_scores": criterion_scores,
        "suggested_total": suggested_total,
        "confidence": overall_confidence,
        "quality_band": band,
        "review_flags": review_flags,
        "reference_alignment": round(reference_score, 4) if reference_score > 0 else None,
        "feedback": " ".join(feedback_parts),
    }


def calculate_submission_grades(
    evaluation: Evaluation,
    submission: Submission,
    chunks: List[SubmissionChunk],
    relevance_results: List[RelevanceResult],
    similarity_data: Optional[Dict[str, Any]] = None,
    review_thresholds: Optional[Dict[str, Any]] = None,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> Dict[str, Any]:
    questions = sorted(evaluation.questions or [], key=lambda q: q.order)
    if not questions:
        return {
            "question_grades": {},
            "suggested_total": 0.0,
            "confidence": 0.0,
            "quality_band": classify_quality_band(0.0),
            "review_flags": ["no_questions"],
            "feedback": "No questions defined for this evaluation.",
        }

    relevance_by_qid = {r.question_id: r for r in relevance_results}
    question_grades = {}
    cumulative_total = 0.0
    cumulative_max = 0.0
    all_flags = set()
    all_confidences = []

    for question in questions:
        rel = relevance_by_qid.get(question.id)
        grade_data = calculate_provisional_grades(
            evaluation, question, submission, chunks, rel,
            similarity_data=similarity_data,
            review_thresholds=review_thresholds,
            model_name=model_name,
        )
        question_grades[str(question.id)] = {
            "question_order": question.order,
            "question_prompt": question.prompt[:200],
            **grade_data,
        }
        cumulative_total += grade_data["suggested_total"]
        criteria = question.rubric_criteria or []
        cumulative_max += sum(c.max_points for c in criteria) if criteria else evaluation.max_marks
        all_flags.update(grade_data.get("review_flags", []))
        all_confidences.append(grade_data["confidence"])

    overall_ratio = cumulative_total / cumulative_max if cumulative_max > 0 else 0.0
    overall_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.5
    overall_band = classify_quality_band(overall_ratio)

    return {
        "question_grades": question_grades,
        "suggested_total": round(cumulative_total, 2),
        "max_possible": round(cumulative_max, 2),
        "confidence": overall_confidence,
        "quality_band": overall_band,
        "review_flags": sorted(all_flags),
        "feedback": f"Overall: {round(cumulative_total, 2)} / {round(cumulative_max, 2)} ({overall_band['label']}). "
                    + " | ".join(
                        f"Q{qd['question_order']}: {qd['suggested_total']}"
                        for qd in question_grades.values()
                    ),
    }


def get_submission_similarity_data(
    db: Session,
    submission_id: UUID,
    evaluation_id: UUID,
) -> Dict[str, Any]:
    comparisons = db.query(Comparison).filter(
        Comparison.evaluation_id == evaluation_id,
        Comparison.status == "completed",
        (Comparison.submission_a_id == submission_id) | (Comparison.submission_b_id == submission_id),
    ).all()

    if not comparisons:
        return {"max_similarity": 0.0, "avg_similarity": 0.0, "flagged_pairs": 0}

    max_sim = 0.0
    total_sim = 0.0
    flagged = 0
    for comp in comparisons:
        scores = [s for s in [comp.exact_score, comp.lexical_score, comp.semantic_score] if s is not None]
        if scores:
            pair_max = max(scores)
            max_sim = max(max_sim, pair_max)
            total_sim += pair_max
            if pair_max >= 0.70:
                flagged += 1

    return {
        "max_similarity": round(max_sim, 4),
        "avg_similarity": round(total_sim / len(comparisons), 4) if comparisons else 0.0,
        "flagged_pairs": flagged,
        "total_comparisons": len(comparisons),
    }


def compute_batch_statistics(
    grading_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not grading_results:
        return {
            "count": 0,
            "mean_score": 0.0,
            "median_score": 0.0,
            "min_score": 0.0,
            "max_score": 0.0,
            "std_dev": 0.0,
            "band_distribution": {},
            "flagged_count": 0,
            "pending_review_count": 0,
        }

    scores = [r["suggested_total"] for r in grading_results]
    scores.sort()
    n = len(scores)
    mean = sum(scores) / n
    median = scores[n // 2] if n % 2 == 1 else (scores[n // 2 - 1] + scores[n // 2]) / 2
    variance = sum((s - mean) ** 2 for s in scores) / n
    std_dev = variance ** 0.5

    band_dist: Dict[str, int] = {}
    flagged_count = 0
    for r in grading_results:
        band = r.get("quality_band", {}).get("band", "unknown")
        band_dist[band] = band_dist.get(band, 0) + 1
        if r.get("review_flags"):
            flagged_count += 1

    return {
        "count": n,
        "mean_score": round(mean, 2),
        "median_score": round(median, 2),
        "min_score": round(min(scores), 2),
        "max_score": round(max(scores), 2),
        "std_dev": round(std_dev, 2),
        "band_distribution": band_dist,
        "flagged_count": flagged_count,
    }
