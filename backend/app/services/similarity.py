from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import math
import logging

logger = logging.getLogger(__name__)

# Model configuration
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_model_cache = None


def get_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL):
    """
    Load and cache the sentence-transformers model (model/provider abstraction).
    Loads on demand with graceful handling if offline or unavailable.
    """
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading semantic embedding model: %s", model_name)
        _model_cache = SentenceTransformer(model_name)
        return _model_cache
    except Exception as e:
        logger.warning("Failed to load SentenceTransformer model '%s': %s. Semantic similarity will use robust fallback.", model_name, e)
        return None


def calculate_exact_similarity(text_a: str, text_b: str, window_size: int = 5) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Calculate exact overlapping shingles / matching passages between two texts.
    Returns exact score (0.0 to 1.0) and matched passage evidence.
    """
    words_a = text_a.lower().split()
    words_b = text_b.lower().split()

    if not words_a or not words_b:
        return 0.0, []

    shingles_a = set(" ".join(words_a[i:i+window_size]) for i in range(len(words_a) - window_size + 1))
    shingles_b = set(" ".join(words_b[i:i+window_size]) for i in range(len(words_b) - window_size + 1))

    if not shingles_a or not shingles_b:
        common = set(words_a).intersection(set(words_b))
        score = len(common) / max(len(set(words_a)), len(set(words_b)), 1)
        return float(score), []

    intersection = shingles_a.intersection(shingles_b)
    union = shingles_a.union(shingles_b)
    exact_score = len(intersection) / len(union) if union else 0.0

    matched_passages = []
    for shingle in intersection:
        if len(shingle) > 10:
            matched_passages.append({
                "match_type": "exact",
                "similarity": 1.0,
                "text_a_excerpt": shingle,
                "text_b_excerpt": shingle,
            })

    return float(exact_score), matched_passages


def calculate_lexical_similarity(text_a: str, text_b: str) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Calculate TF-IDF cosine similarity for lexical overlap.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0, []

    vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
    try:
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except Exception:
        score = 0.0

    return float(score), []


def calculate_semantic_similarity(text_a: str, text_b: str, model_name: str = DEFAULT_EMBEDDING_MODEL) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Calculate genuine semantic similarity using dense vector embeddings
    generated via pretrained sentence-transformer models (e.g. all-MiniLM-L6-v2).
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0, []

    model = get_embedding_model(model_name)
    if model is not None:
        try:
            # Generate real dense vector embeddings
            embeddings = model.encode([text_a, text_b], convert_to_numpy=True)
            # Calculate cosine similarity between embedding vectors
            score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(max(0.0, min(1.0, score))), []
        except Exception as e:
            logger.error("Error generating embeddings with SentenceTransformer: %s", e)

    # Fallback to robust character TF-IDF semantic approximation if model is unavailable
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1)
    try:
        matrix = vectorizer.fit_transform([text_a, text_b])
        score = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        score = min(1.0, score * 1.15)
    except Exception:
        score = 0.0

    return float(score), []


def filter_common_content(text: str, question_prompt: str) -> str:
    """
    Filter common assignment questions, boilerplate, and instructions from comparison text.
    """
    if not text:
        return ""
    
    cleaned = text.lower().replace(question_prompt.lower(), "")
    
    boilerplate = [
        "explain their differences",
        "provide two examples",
        "answer:",
        "solution:",
        "question",
    ]
    for phrase in boilerplate:
        cleaned = cleaned.replace(phrase, "")

    return cleaned.strip()
