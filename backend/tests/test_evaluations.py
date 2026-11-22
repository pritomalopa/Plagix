import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app

client = TestClient(app)


def helper_register_user(name: str, email: str) -> str:
    """Helper to register user and return access token cookie value."""
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "name": name,
        "tenant_name": f"{name}'s School"
    })
    assert res.status_code == 201
    return res.cookies.get("access_token")


def test_evaluation_crud_flow():
    token = helper_register_user("Prof. Alice", f"alice_{uuid4()}@test.edu")
    client.cookies.set("access_token", token)

    # 1. Create Evaluation with Question and Rubric
    eval_payload = {
        "title": "Calculus Final Exam",
        "language": "en",
        "max_marks": 100,
        "settings": {"allow_review": True},
        "questions": [
            {
                "order": 1,
                "prompt": "Evaluate the derivative of x^2 * sin(x).",
                "instructions": "Show all steps.",
                "reference_answer": "2x*sin(x) + x^2*cos(x)",
                "expected_concepts": {"product_rule": "mandatory"},
                "citation_policy": "none",
                "rubric_criteria": [
                    {
                        "criterion": "Derivative calculation",
                        "description": "Correct application of product rule",
                        "max_points": 70,
                        "weight": 1.0,
                        "order": 1
                    },
                    {
                        "criterion": "Algebraic simplification",
                        "description": "Simplified final expression",
                        "max_points": 30,
                        "weight": 1.0,
                        "order": 2
                    }
                ]
            }
        ]
    }

    create_res = client.post("/api/evaluations", json=eval_payload)
    assert create_res.status_code == 201
    eval_data = create_res.json()
    assert eval_data["title"] == "Calculus Final Exam"
    assert eval_data["max_marks"] == 100
    assert len(eval_data["questions"]) == 1
    assert len(eval_data["questions"][0]["rubric_criteria"]) == 2
    eval_id = eval_data["id"]
    q_id = eval_data["questions"][0]["id"]
    rc_id = eval_data["questions"][0]["rubric_criteria"][0]["id"]

    # 2. List Evaluations
    list_res = client.get("/api/evaluations")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(e["id"] == eval_id for e in list_data["evaluations"])

    # 3. Get Single Evaluation
    get_res = client.get(f"/api/evaluations/{eval_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Calculus Final Exam"

    # 4. Update Evaluation
    update_res = client.patch(f"/api/evaluations/{eval_id}", json={
        "title": "Calculus Final Exam (Updated)"
    })
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Calculus Final Exam (Updated)"

    # 5. Add Question separately
    add_q_res = client.post(f"/api/evaluations/{eval_id}/questions", json={
        "order": 2,
        "prompt": "Explain the Fundamental Theorem of Calculus."
    })
    assert add_q_res.status_code == 201
    new_q_id = add_q_res.json()["id"]

    # 6. Delete Rubric Criterion
    del_rc_res = client.delete(f"/api/evaluations/{eval_id}/questions/{q_id}/rubric/{rc_id}")
    assert del_rc_res.status_code == 204

    # 7. Delete Question
    del_q_res = client.delete(f"/api/evaluations/{eval_id}/questions/{new_q_id}")
    assert del_q_res.status_code == 204

    # 8. Delete Evaluation
    del_eval_res = client.delete(f"/api/evaluations/{eval_id}")
    assert del_eval_res.status_code == 204

    # Verify deleted
    get_deleted = client.get(f"/api/evaluations/{eval_id}")
    assert get_deleted.status_code == 404


def test_rubric_criterion_deletion_persists():
    """
    Regression test: verify that deleting a rubric criterion actually removes it
    from the database and that a subsequent GET request confirms its absence,
    while leaving other criteria intact.
    """
    token = helper_register_user("Prof. Charlie", f"charlie_{uuid4()}@test.edu")
    client.cookies.set("access_token", token)

    eval_payload = {
        "title": "Rubric Deletion Test Exam",
        "language": "en",
        "max_marks": 100,
        "questions": [
            {
                "order": 1,
                "prompt": "Test prompt",
                "rubric_criteria": [
                    {"criterion": "Criterion One", "max_points": 40, "order": 1},
                    {"criterion": "Criterion Two", "max_points": 60, "order": 2}
                ]
            }
        ]
    }

    create_res = client.post("/api/evaluations", json=eval_payload)
    assert create_res.status_code == 201
    eval_data = create_res.json()
    eval_id = eval_data["id"]
    q_id = eval_data["questions"][0]["id"]
    criteria = eval_data["questions"][0]["rubric_criteria"]
    assert len(criteria) == 2
    rc_id_to_delete = criteria[0]["id"]
    rc_id_to_keep = criteria[1]["id"]

    # Delete first criterion
    del_res = client.delete(f"/api/evaluations/{eval_id}/questions/{q_id}/rubric/{rc_id_to_delete}")
    assert del_res.status_code == 204

    # Fetch evaluation in a separate GET request
    get_res = client.get(f"/api/evaluations/{eval_id}")
    assert get_res.status_code == 200
    updated_criteria = get_res.json()["questions"][0]["rubric_criteria"]

    # Verify criterion is absent and other criterion remains intact
    assert len(updated_criteria) == 1
    assert updated_criteria[0]["id"] == rc_id_to_keep
    assert updated_criteria[0]["criterion"] == "Criterion Two"


def test_cross_tenant_evaluation_isolation():
    # Tenant A
    token_a = helper_register_user("Teacher A", f"prof_a_{uuid4()}@test.edu")
    client.cookies.set("access_token", token_a)
    
    eval_res = client.post("/api/evaluations", json={
        "title": "Tenant A Secret Exam",
        "max_marks": 50
    })
    assert eval_res.status_code == 201
    eval_id = eval_res.json()["id"]

    # Tenant B
    token_b = helper_register_user("Teacher B", f"prof_b_{uuid4()}@test.edu")
    client.cookies.set("access_token", token_b)

    # Tenant B tries to read Tenant A evaluation -> 403 Forbidden
    get_res = client.get(f"/api/evaluations/{eval_id}")
    assert get_res.status_code == 403

    # Tenant B tries to update Tenant A evaluation -> 403 Forbidden
    patch_res = client.patch(f"/api/evaluations/{eval_id}", json={"title": "Hacked"})
    assert patch_res.status_code == 403

    # Tenant B tries to delete Tenant A evaluation -> 403 Forbidden
    del_res = client.delete(f"/api/evaluations/{eval_id}")
    assert del_res.status_code == 403


def test_evaluation_validation_errors():
    token = helper_register_user("Prof. Bob", f"bob_{uuid4()}@test.edu")
    client.cookies.set("access_token", token)

    # Missing title and invalid max_marks (negative)
    res = client.post("/api/evaluations", json={
        "title": "",
        "max_marks": -10
    })
    assert res.status_code == 422
