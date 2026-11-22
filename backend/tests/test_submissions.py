import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
import io
import zipfile

from app.main import app

client = TestClient(app)


def helper_register_and_create_eval(name: str, email: str) -> tuple[str, str]:
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "name": name,
        "tenant_name": f"{name}'s Institution"
    })
    assert res.status_code == 201
    token = res.cookies.get("access_token")
    client.cookies.set("access_token", token)

    eval_res = client.post("/api/evaluations", json={
        "title": "Assignment Upload Test",
        "max_marks": 100
    })
    assert eval_res.status_code == 201
    return token, eval_res.json()["id"]


def test_upload_individual_txt_and_pdf():
    token, eval_id = helper_register_and_create_eval("Prof. Newton", f"newton_{uuid4()}@test.edu")

    # Upload individual TXT file
    txt_content = b"This is a sample student answer text for physics assignment."
    response = client.post(
        f"/api/evaluations/{eval_id}/upload",
        files={"files": ("student_one_answer.txt", txt_content, "text/plain")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total"] == 1
    assert data["submissions"][0]["student_label"] == "student_one_answer"
    assert data["submissions"][0]["original_filename"] == "student_one_answer.txt"

    # List submissions
    list_res = client.get(f"/api/evaluations/{eval_id}/submissions")
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1


def test_upload_zip_archive():
    token, eval_id = helper_register_and_create_eval("Prof. Curie", f"curie_{uuid4()}@test.edu")

    # Create in-memory ZIP archive with TXT files inside
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("alice_homework.txt", "Alice's chemistry lab report answer.")
        zf.writestr("bob_report.txt", "Bob's chemistry lab report answer.")
    zip_bytes = zip_buffer.getvalue()

    response = client.post(
        f"/api/evaluations/{eval_id}/upload",
        files={"files": ("homework_batch.zip", zip_bytes, "application/zip")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total"] == 2
    labels = {s["student_label"] for s in data["submissions"]}
    assert "alice_homework" in labels
    assert "bob_report" in labels


def test_duplicate_file_detection():
    token, eval_id = helper_register_and_create_eval("Prof. Darwin", f"darwin_{uuid4()}@test.edu")

    content = b"Identical student submission content."
    # Upload first time
    res1 = client.post(
        f"/api/evaluations/{eval_id}/upload",
        files={"files": ("essay.txt", content, "text/plain")}
    )
    assert res1.status_code == 201
    assert res1.json()["total"] == 1

    # Upload duplicate file (same content)
    res2 = client.post(
        f"/api/evaluations/{eval_id}/upload",
        files={"files": ("essay_copy.txt", content, "text/plain")}
    )
    assert res2.status_code == 201
    # Duplicate should be skipped
    assert res2.json()["total"] == 0


def test_unsupported_file_extension_rejection():
    token, eval_id = helper_register_and_create_eval("Prof. Turing", f"turing_{uuid4()}@test.edu")

    response = client.post(
        f"/api/evaluations/{eval_id}/upload",
        files={"files": ("malware.exe", b"fake executable content", "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_cross_tenant_submission_isolation():
    token_a, eval_a_id = helper_register_and_create_eval("Teacher A", f"t_a_{uuid4()}@test.edu")
    
    # Upload submission to evaluation A
    client.post(
        f"/api/evaluations/{eval_a_id}/upload",
        files={"files": ("answer.txt", b"answer", "text/plain")}
    )

    # Register Teacher B
    token_b, eval_b_id = helper_register_and_create_eval("Teacher B", f"t_b_{uuid4()}@test.edu")

    # Teacher B tries to list submissions of Evaluation A -> 403 Forbidden
    res = client.get(f"/api/evaluations/{eval_a_id}/submissions")
    assert res.status_code == 403
