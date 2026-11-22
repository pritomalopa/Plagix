import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.base import Base
from app.db.session import get_db
import app.db.session
from app.workers.celery_app import celery_app

# Configure Celery for synchronous execution in tests
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
)

# Use SQLite in-memory for testing without requiring external PostgreSQL service
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Point session local to test session local
app.db.session.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_dependency(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    fastapi_app.dependency_overrides[get_db] = _override_get_db
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(fastapi_app)
