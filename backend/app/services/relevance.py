from typing import List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.evaluation import Evaluation
from app.models.question import Question
from app.models.submission import Submission
from app.models.submission_chunk import SubmissionChunk
from app.models.relevance_result import RelevanceResult
from app.services.similarity import get_embedding_model, DEFAULT_EMBEDDING_MODEL
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


def analyze_answer_relevance(
    question: Question,
    submission: Submission,
    chunks: List[SubmissionChunk],
    model_name: str = DEFAULT_EMBEDDING_MODEL
) -> Dict[str, Any]:
    """
    Evaluate answer relevance and concept coverage against the question prompt,
    reference answer, and expected concepts using real semantic embeddings.
    """
    answer_text = " ".join(c.original_text for c in chunks)
    if not answer_text.strip():
        return {
            "category": "off_topic",
            "score": 0.0,
            "confidence": 1.0,
            "rationale": "Submission is empty or contains no extractable text.",
            "evidence": [],
            "concepts_coverage": [],
            "model_version": model_name
        }

    question_text = f"{question.prompt} {question.instructions or ''} {question.reference_answer or ''}"
    
    # Extract expected concepts from question configuration or derive them
    expected_concepts = []
    if question.expected_concepts:
        if isinstance(question.expected_concepts, dict):
            expected_concepts = list(question.expected_concepts.keys())
        elif isinstance(question.expected_concepts, list):
            expected_concepts = question.expected_concepts

    model = get_embedding_model(model_name)
    semantic_score = 0.5
    evidence_excerpts = []

    if model is not None:
        try:
            # Encode question/reference vs answer
            embeddings = model.encode([question_text, answer_text], convert_to_numpy=True)
            semantic_score = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
            semantic_score = max(0.0, min(1.0, semantic_score))

            # Find best matching paragraph/chunk as evidence excerpt
            if chunks:
                chunk_texts = [c.original_text for c in chunks]
                chunk_embeddings = model.encode(chunk_texts, convert_to_numpy=True)
                similarities = cosine_similarity([embeddings[0]], chunk_embeddings)[0]
                best_idx = int(similarities.argmax())
                best_chunk = chunks[best_idx]
                evidence_excerpts.append({
                    "text": best_chunk.original_text[:300],
                    "page": best_chunk.page,
                    "score": float(similarities[best_idx])
                })
        except Exception as e:
            logger.error("Error generating relevance embeddings: %s", e)
    else:
        # Fallback word overlap score
        q_words = set(question_text.lower().split())
        a_words = set(answer_text.lower().split())
        common = q_words.intersection(a_words)
        semantic_score = len(common) / max(len(q_words), 1)

    # Determine relevance category
    if semantic_score >= 0.65:
        category = "relevant"
    elif semantic_score >= 0.40:
        category = "partially_relevant"
    elif semantic_score >= 0.20:
        category = "uncertain"
    else:
        category = "off_topic"

    # Evaluate concept coverage
    concepts_coverage = []
    for concept in expected_concepts:
        # Check semantic similarity between concept and answer chunks
        concept_score = 0.5
        if model is not None:
            try:
                c_emb = model.encode([concept], convert_to_numpy=True)
                a_emb = model.encode([answer_text], convert_to_numpy=True)
                concept_score = float(cosine_similarity(c_emb, a_emb)[0][0])
            except Exception:
                pass
        else:
            concept_score = 1.0 if concept.lower() in answer_text.lower() else 0.2

        if concept_score >= 0.6:
            status = "present"
            explanation = f"Concept '{concept}' is demonstrated with good semantic alignment."
        elif concept_score >= 0.4:
            status = "partially_covered"
            explanation = f"Concept '{concept}' is mentioned or partially addressed."
        else:
            status = "missing"
            explanation = f"Concept '{concept}' is missing or inadequately explained."

        concepts_coverage.append({
            "concept": concept,
            "status": status,
            "confidence": float(concept_score),
            "explanation": explanation
        })

    confidence = 0.85 if model is not None else 0.60
    rationale = f"Answer demonstrates {semantic_score:.1%} semantic alignment with question guidelines."

    return {
        "category": category,
        "score": semantic_score,
        "confidence": confidence,
        "rationale": rationale,
        "evidence": evidence_excerpts,
        "concepts_coverage": concepts_coverage,
        "model_version": model_name
    }
