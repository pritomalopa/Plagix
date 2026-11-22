import pytest
from app.services.similarity import (
    calculate_exact_similarity,
    calculate_lexical_similarity,
    calculate_semantic_similarity,
    get_embedding_model,
    DEFAULT_EMBEDDING_MODEL
)


def test_embedding_model_initialization():
    model = get_embedding_model(DEFAULT_EMBEDDING_MODEL)
    # If internet/huggingface cache is available, model loads. If offline, it returns None gracefully.
    if model is not None:
        embeddings = model.encode(["Test sentence one", "Test sentence two"])
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384  # all-MiniLM-L6-v2 dimension is 384


def test_semantic_similarity_paraphrase():
    text_a = "Supervised learning algorithms are trained using labeled example datasets."
    text_b = "Annotated training examples are used to fit predictive models in supervised machine learning."
    text_c = "Quantum computing utilizes qubits and superposition phenomena."

    score_para, _ = calculate_semantic_similarity(text_a, text_b)
    score_unrelated, _ = calculate_semantic_similarity(text_a, text_c)

    # Paraphrase score should be higher than unrelated text score
    assert score_para > score_unrelated
