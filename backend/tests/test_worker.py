"""
Unit tests for the Celery worker task execution.
"""

from worker import write_log_celery


def test_write_log_celery_execution(monkeypatch, tmp_path):
    test_log = tmp_path / "test_log.txt"
    monkeypatch.setenv("CELERY_LOG_FILE", str(test_log))
    monkeypatch.setattr("worker.settings.TASK_SIMULATION_SECONDS", 0)
    monkeypatch.setattr("worker.settings.ENABLE_REAL_EMAIL", False)

    # In Celery with bind=True, calling .apply() executes locally in eager mode
    # or .run(mock_self, ...) invokes the underlying function directly.
    result = write_log_celery.apply(args=["Notification sent to test@example.com"]).get()
    assert "Task completed: Notification sent to test@example.com" in result
    assert test_log.exists()
    content = test_log.read_text(encoding="utf-8")
    assert "Notification sent to test@example.com" in content
