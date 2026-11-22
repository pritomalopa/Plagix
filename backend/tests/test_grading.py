import pytest
from fastapi.testclient import TestClient
from uuid import UUID, uuid4

from app.main import app
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.question import Question
from app.models.rubric_criterion import RubricCriterion
from app.models.submission import Submission
from app.models.submission_chunk import SubmissionChunk
from app.core.security import get_password_hash, create_access_token
from app.workers.grading_tasks import run_evaluation_grading_task

client = TestClient(app)


def helper_setup_eval_with_rubric(name: str, email: str, texts: dict) -> tuple[str, str, dict]:
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
            title="Rubric Grading Test Exam",
            max_marks=100,
            status="created"
        )
        db.add(evaluation)
        db.flush()

        question = Question(
            evaluation_id=evaluation.id,
            order=1,
            prompt="Explain the core components of neural networks and backpropagation.",
            reference_answer="Neural networks consist of input, hidden, and output layers with weights and biases. Backpropagation uses gradient descent and chain rule to update weights.",
            expected_concepts=["weights", "biases", "backpropagation", "gradient descent"]
        )
        db.add(question)
        db.flush()

        criterion1 = RubricCriterion(
            question_id=question.id,
            criterion="Understanding of Network Layers",
            description="Explains input, hidden, and output layers correctly.",
            max_points=50,
            weight=1.0,
            expected_evidence="Mention of layers, weights, and biases.",
            order=1
        )
        criterion2 = RubricCriterion(
            question_id=question.id,
            criterion="Explanation of Backpropagation",
            description="Describes gradient descent and parameter updates.",
            max_points=50,
            weight=1.0,
            expected_evidence="Gradient descent, loss minimization, weight updates.",
            order=2
        )
        db.add(criterion1)
        db.add(criterion2)
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


def test_grading_pipeline_and_teacher_override():
    texts = {
        "student_excellent": "Neural networks are composed of input, hidden, and output layers connected by weights and biases. Backpropagation optimizes these weights using gradient descent and the chain rule of calculus.",
        "student_partial": "Neural networks have layers and weights. Backpropagation helps train the model.",
        "student_poor": "Computers process data using electricity and microchips."
    }

    eval_id, sub_map = helper_setup_eval_with_rubric(
        "Dr. Turing", f"turing_{uuid4()}@test.edu", texts
    )

    # 1. Trigger provisional grading via API
    start_res = client.post(f"/api/evaluations/{eval_id}/grade")
    assert start_res.status_code == 202

    # 2. Run Celery grading task synchronously
    run_evaluation_grading_task(eval_id)

    # 3. Retrieve grading results with batch statistics
    results_res = client.get(f"/api/evaluations/{eval_id}/grading-results")
    assert results_res.status_code == 200
    data = results_res.json()
    assert data["total"] == 3
    assert data["batch_statistics"]["count"] == 3
    assert data["batch_statistics"]["mean_score"] > 0

    # 4. Test teacher override on student_partial submission
    sub_id = sub_map["student_partial"]
    override_payload = {
        "teacher_final_score": 75.0,
        "override_reason": "Student correctly understood foundational concepts but missed calculus details.",
        "criterion_scores_override": {
            "adjustment_note": "Manually reviewed by instructor."
        }
    }
    override_res = client.patch(f"/api/evaluations/submissions/{sub_id}/grade", json=override_payload)
    assert override_res.status_code == 200
    override_data = override_res.json()
    assert override_data["teacher_final_score"] == 75.0
    assert override_data["status"] == "approved"
    assert override_data["override_reason"] is not None

    # 5. Retrieve single submission grade detail
    detail_res = client.get(f"/api/evaluations/submissions/{sub_id}/grade")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["status"] == "approved"
    assert detail_data["teacher_final_score"] == 75.0


def test_cross_tenant_grading_access():
    eval_a_id, sub_map = helper_setup_eval_with_rubric(
        "Prof A", f"pa_{uuid4()}@test.edu", {"s1": "Neural networks work with layers."}
    )

    db = SessionLocal()
    try:
        tenant = Tenant(name="Another Univ", plan="free")
        db.add(tenant)
        db.flush()
        user = User(
            tenant_id=tenant.id,
            email=f"pb_{uuid4()}@test.edu",
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

    # Teacher B tries to grade or access Evaluation A -> 403 or 404
    res = client.get(f"/api/evaluations/{eval_a_id}/grading-results")
    assert res.status_code in (403, 404)
