import pytest
from fastapi.testclient import TestClient
from uuid import UUID, uuid4

from app.main import app
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.question import Question
from app.models.submission import Submission
from app.models.submission_chunk import SubmissionChunk
from app.core.security import get_password_hash, create_access_token
from app.workers.relevance_tasks import run_evaluation_relevance_task

client = TestClient(app)


def helper_setup_eval_with_relevance_data(name: str, email: str, question_prompt: str, expected_concepts: list, texts: dict) -> tuple[str, str, dict]:
    db = SessionLocal()
    try:
        tenant = Tenant(name=f"{name}'s Univ", plan="free")
        db.add(tenant)
        db.flush()

        user = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=get_password_hash("Password123!"),
            role="teacher",
            status="active"
        )
        db.add(user)
        db.flush()
        user_id_str = str(user.id)

        evaluation = Evaluation(
            tenant_id=tenant.id,
            owner_id=user.id,
            title="Relevance Test Exam",
            max_marks=100,
            status="created"
        )
        db.add(evaluation)
        db.flush()

        question = Question(
            evaluation_id=evaluation.id,
            order=1,
            prompt=question_prompt,
            expected_concepts={c: "essential" for c in expected_concepts}
        )
        db.add(question)
        db.flush()

        eval_id_str = str(evaluation.id)
        eval_uuid = evaluation.id

        sub_map = {}
        for label, text in texts.items():
            sub = Submission(
                evaluation_id=eval_uuid,
                student_label=label,
                original_filename=f"{label}.txt",
                file_hash=uuid4().hex,
                storage_key=f"storage/test/{label}.txt",
                extraction_status="completed"
            )
            db.add(sub)
            db.flush()

            chunk = SubmissionChunk(
                submission_id=sub.id,
                page=1,
                paragraph=1,
                offset=0,
                original_text=text,
                normalized_text=text.lower()
            )
            db.add(chunk)
            sub_map[label] = str(sub.id)

        db.commit()
    finally:
        db.close()

    token = create_access_token(user_id_str)
    cookie_value = f"Bearer {token}"
    client.cookies.set("access_token", cookie_value)

    return cookie_value, eval_id_str, sub_map


def test_relevance_and_concept_analysis_pipeline():
    prompt = "Explain photosynthesis and its two main stages: light-dependent reactions and the Calvin cycle."
    concepts = ["chlorophyll", "light-dependent reactions", "Calvin cycle", "ATP"]
    texts = {
        "student_relevant": "Photosynthesis is the process by which plants convert sunlight into energy using chlorophyll. It involves light-dependent reactions to generate ATP and the Calvin cycle to fix carbon.",
        "student_partial": "Plants make food using sunlight and water in leaves.",
        "student_off_topic": "Quantum mechanics explores the probabilistic behavior of subatomic particles at absolute zero."
    }

    token, eval_id, sub_map = helper_setup_eval_with_relevance_data(
        "Prof. Darwin", f"darwin_{uuid4()}@test.edu", prompt, concepts, texts
    )

    # 1. Trigger relevance analysis via API with explicit cookies
    start_res = client.post(f"/api/evaluations/{eval_id}/relevance", cookies={"access_token": token})
    assert start_res.status_code == 202

    # 2. Run Celery relevance task synchronously for verification
    run_evaluation_relevance_task(eval_id)

    # 3. Retrieve relevance results
    get_res = client.get(f"/api/evaluations/{eval_id}/relevance", cookies={"access_token": token})
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["total"] == 3

    results_by_label = {item["student_label"]: item for item in data["relevance_results"]}
    
    # Relevant student check
    rel_item = results_by_label["student_relevant"]
    assert rel_item["category"] in ("relevant", "partially_relevant")
    assert len(rel_item["evidence"]["concepts_coverage"]) == len(concepts)

    # Off-topic student check
    off_item = results_by_label["student_off_topic"]
    assert off_item["category"] == "off_topic"


def test_cross_tenant_relevance_access():
    token_a, eval_a_id, _ = helper_setup_eval_with_relevance_data(
        "Teacher 1", f"t1_{uuid4()}@test.edu", "Explain X", ["X"], {"s1": "X"}
    )

    db = SessionLocal()
    try:
        tenant = Tenant(name="Other Univ", plan="free")
        db.add(tenant)
        db.flush()
        user = User(
            tenant_id=tenant.id,
            email=f"t2_{uuid4()}@test.edu",
            password_hash=get_password_hash("Password123!"),
            role="teacher",
            status="active"
        )
        db.add(user)
        db.commit()
        token_b = create_access_token(str(user.id))
    finally:
        db.close()

    client.cookies.set("access_token", f"Bearer {token_b}")

    # Teacher 2 tries to access relevance of Evaluation A -> 403 or 404
    res = client.get(f"/api/evaluations/{eval_a_id}/relevance")
    assert res.status_code in (403, 404)
