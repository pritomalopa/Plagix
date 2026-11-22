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
from celery.app.task import Task

# Keep original production celery configuration intact for test_worker.py,
# but make .delay() and .apply_async() execute synchronously during tests.
Task.delay = lambda self, *args, **kwargs: self.apply(args=args, kwargs=kwargs)
Task.apply_async = lambda self, args=None, kwargs=None, **options: self.apply(args=args or (), kwargs=kwargs or {})

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
