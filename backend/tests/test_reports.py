import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)


def test_reports_export_endpoints():
    db = SessionLocal()
    try:
        tenant = Tenant(name="Report Univ", plan="free")
        db.add(tenant)
        db.flush()

        user = User(
            tenant_id=tenant.id,
            email=f"reporter_{uuid4()}@test.edu",
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
            title="Export Test Exam",
            max_marks=100,
            status="created"
        )
        db.add(evaluation)
        db.flush()
        eval_id_str = str(evaluation.id)

        sub = Submission(
            evaluation_id=evaluation.id,
            student_label="student_one",
            original_filename="exam_one.txt",
            file_hash=uuid4().hex,
            storage_key="storage/test/exam_one.txt",
            extraction_status="completed"
        )
        db.add(sub)
        db.commit()
    finally:
        db.close()

    token = create_access_token(user_id_str)
    client.cookies.set("access_token", f"Bearer {token}")

    # Test CSV export
    csv_res = client.get(f"/api/evaluations/{eval_id_str}/reports/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Evaluation Title" in csv_res.text
    assert "student_one" in csv_res.text

    # Test Summary JSON report
    summary_res = client.get(f"/api/evaluations/{eval_id_str}/reports/summary")
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["title"] == "Export Test Exam"
    assert summary_data["total_submissions"] == 1
