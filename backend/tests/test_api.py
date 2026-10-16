"""
Unit and integration tests for API endpoints:
- POST /notify/
- GET /task_status/{task_id}
Tests edge cases, validation, mocked Celery results, and broker errors.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_notify_success(mocker):
    # Mock write_log_celery.delay
    mock_task = MagicMock()
    mock_task.id = "mocked-uuid-12345"
    mocker.patch("main.write_log_celery.delay", return_value=mock_task)

    response = client.post("/notify/?email=engineer@example.com")
    assert response.status_code == 202
    data = response.json()
    assert data["task_id"] == "mocked-uuid-12345"
    assert "Notification sent to engineer@example.com" or "Email will be sent to engineer@example.com" in data["message"]


def test_notify_invalid_email():
    response = client.post("/notify/?email=not-an-email")
    assert response.status_code == 422
    assert "Invalid email format" in response.json()["detail"]


def test_notify_empty_email():
    response = client.post("/notify/?email=")
    assert response.status_code == 400


def test_notify_broker_down(mocker):
    mocker.patch("main.write_log_celery.delay", side_effect=Exception("Redis connection refused"))
    response = client.post("/notify/?email=valid@example.com")
    assert response.status_code == 503
    assert "Message broker unavailable" in response.json()["detail"]


def test_task_status_completed(mocker):
    mock_async_result = MagicMock()
    mock_async_result.ready.return_value = True
    mock_async_result.successful.return_value = True
    mock_async_result.result = "Task completed: Notification sent to test@example.com"
    mocker.patch("main.AsyncResult", return_value=mock_async_result)

    response = client.get("/task_status/task-123")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "task-123"
    assert data["status"] == "completed"
    assert "Task completed" in data["result"]


def test_task_status_failed(mocker):
    mock_async_result = MagicMock()
    mock_async_result.ready.return_value = True
    mock_async_result.successful.return_value = False
    mock_async_result.failed.return_value = True
    mock_async_result.result = Exception("Worker timeout")
    mocker.patch("main.AsyncResult", return_value=mock_async_result)

    response = client.get("/task_status/task-456")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "task-456"
    assert data["status"] == "failed"


def test_task_status_in_progress(mocker):
    mock_async_result = MagicMock()
    mock_async_result.ready.return_value = False
    mock_async_result.failed.return_value = False
    mock_async_result.state = "PENDING"
    mocker.patch("main.AsyncResult", return_value=mock_async_result)

    response = client.get("/task_status/task-789")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "task-789"
    assert data["status"] == "in progress"
