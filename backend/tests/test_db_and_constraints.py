import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

from app.main import app
from app.core.config import settings
from app.db.base import Base
from app.models import Tenant, User, Evaluation, Submission, Comparison

client = TestClient(app)


def test_health_live():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["product"] == "PLAGIX"


def test_database_connection_and_constraints():
    # Use test database URL from environment or fallback
    test_db_url = os.getenv("TEST_DATABASE_URL", settings.database_url)
    engine = create_engine(test_db_url)
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionTesting()
    try:
        # 1. Verify table count (should have 14 tables)
        result = db.execute(text("""
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """))
        table_count = result.scalar()
        assert table_count >= 14, f"Expected at least 14 tables, found {table_count}"

        # 2. Test Tenant & User creation
        tenant_id = uuid4()
        user_id = uuid4()
        eval_id = uuid4()
        sub1_id = uuid4()
        sub2_id = uuid4()

        tenant = Tenant(id=tenant_id, name="Test University", plan="free")
        db.add(tenant)
        db.commit()

        user = User(
            id=user_id,
            tenant_id=tenant_id,
            email=f"teacher_{uuid4()}@test.edu",
            password_hash="hashed_pw",
            role="teacher"
        )
        db.add(user)
        db.commit()

        evaluation = Evaluation(
            id=eval_id,
            tenant_id=tenant_id,
            owner_id=user_id,
            title="Midterm Exam",
            max_marks=100
        )
        db.add(evaluation)
        db.commit()

        sub1 = Submission(
            id=sub1_id,
            evaluation_id=eval_id,
            student_label="Alice",
            original_filename="alice.pdf",
            file_hash=f"hash1_{uuid4()}",
            storage_key="s3://key1"
        )
        sub2 = Submission(
            id=sub2_id,
            evaluation_id=eval_id,
            student_label="Bob",
            original_filename="bob.pdf",
            file_hash=f"hash2_{uuid4()}",
            storage_key="s3://key2"
        )
        db.add_all([sub1, sub2])
        db.commit()

        # 3. Test Canonical Pair Constraint (submission_a_id < submission_b_id)
        # Ensure sub1_id < sub2_id for valid pair, or test failure when sub1_id > sub2_id
        if sub1_id > sub2_id:
            sub1_id, sub2_id = sub2_id, sub1_id

        # Valid canonical comparison
        comp = Comparison(
            evaluation_id=eval_id,
            submission_a_id=sub1_id,
            submission_b_id=sub2_id,
            lexical_score=0.85,
            status="completed"
        )
        db.add(comp)
        db.commit()

        # 4. Test Duplicate Comparison (Unique constraint violation)
        comp_dup = Comparison(
            evaluation_id=eval_id,
            submission_a_id=sub1_id,
            submission_b_id=sub2_id,
            lexical_score=0.85,
            status="completed"
        )
        db.add(comp_dup)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        # 5. Test Reversed Pair Constraint violation (check_canonical_pair check constraint)
        # If we try to insert where submission_a_id > submission_b_id
        comp_reversed = Comparison(
            evaluation_id=eval_id,
            submission_a_id=sub2_id,
            submission_b_id=sub1_id,
            lexical_score=0.85,
            status="completed"
        )
        db.add(comp_reversed)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    finally:
        db.close()
        engine.dispose()
