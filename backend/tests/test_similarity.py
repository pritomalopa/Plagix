import pytest
from fastapi.testclient import TestClient
from uuid import UUID, uuid4

from app.main import app
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.submission_chunk import SubmissionChunk
from app.core.security import get_password_hash, create_access_token
from app.workers.similarity_tasks import run_evaluation_comparison_task

client = TestClient(app)


def helper_setup_eval_with_submissions(name: str, email: str, texts: dict) -> tuple[str, str, dict]:
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
            title="Plagiarism Test Exam",
            max_marks=100,
            status="created"
        )
        db.add(evaluation)
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
    client.cookies.set("access_token", f"Bearer {token}")

    return eval_id_str, sub_map


def test_similarity_analysis_pipeline():
    texts = {
        "student_a": "Supervised learning uses labeled training data to learn a mapping function from input variables to output variables. [Source A]",
        "student_b": "Supervised learning uses labeled training data to learn a mapping function from input variables to output variables. [Source B]", # Near copy
        "student_c": "In supervised learning, algorithms are trained using annotated datasets to map inputs to outputs.", # Paraphrase / semantic
        "student_d": "Quantum computing utilizes qubits and superposition phenomena to solve complex mathematical equations." # Unrelated
    }

    eval_id, sub_map = helper_setup_eval_with_submissions(
        "Prof. Einstein", f"einstein_{uuid4()}@test.edu", texts
    )

    # 1. Trigger similarity analysis via API
    start_res = client.post(f"/api/evaluations/{eval_id}/compare")
    assert start_res.status_code == 202

    # 2. Run Celery comparison task synchronously for verification
    run_evaluation_comparison_task(eval_id)

    # 3. Retrieve comparisons list
    list_res = client.get(f"/api/evaluations/{eval_id}/comparisons")
    assert list_res.status_code == 200
    comparisons_data = list_res.json()
    assert comparisons_data["total"] > 0

    # Verify A vs B (near copy) has high lexical/exact score
    comp_ab = next(
        (c for c in comparisons_data["comparisons"] 
         if {c["submission_a"]["id"], c["submission_b"]["id"]} == {sub_map["student_a"], sub_map["student_b"]}),
        None
    )
    assert comp_ab is not None
    assert comp_ab["exact_score"] > 0.8
    assert comp_ab["lexical_score"] > 0.8

    # 4. Retrieve matched passage evidence for A vs B
    passages_res = client.get(f"/api/evaluations/{eval_id}/comparisons/{comp_ab['id']}/passages")
    assert passages_res.status_code == 200
    passages_data = passages_res.json()
    assert "warning" in passages_data
    assert len(passages_data["matched_passages"]) > 0


def test_cross_tenant_similarity_access():
    eval_a_id, _ = helper_setup_eval_with_submissions(
        "Teacher 1", f"t1_{uuid4()}@test.edu", {"s1": "text"}
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

    # Teacher 2 tries to access comparisons of Evaluation A -> 404 Not Found
    res = client.get(f"/api/evaluations/{eval_a_id}/comparisons")
    assert res.status_code in (403, 404)
