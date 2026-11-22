import pytest
from app.workers.celery_app import celery_app
from app.workers.tasks import diagnostic_ping


def test_celery_configuration():
    assert celery_app.conf.broker_url == "redis://redis:6379/0" or "redis" in celery_app.conf.broker_url
    assert celery_app.conf.task_serializer == "json"
    assert "app.workers.tasks" in celery_app.conf.imports or len(celery_app.tasks) > 0


def test_diagnostic_ping_task():
    # Test task execution synchronously
    result = diagnostic_ping.apply(args=("hello test",))
    assert result.status == "SUCCESS"
    data = result.get()
    assert data["status"] == "success"
    assert data["message"] == "pong: hello test"
    assert "task_id" in data
