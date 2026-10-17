"""
Celery Worker Root Entry Point
Exposes Celery application and worker tasks for Render, container, and CLI runners.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from backend.worker import celery, write_log_celery, process_notification_job, send_real_email

__all__ = ["celery", "write_log_celery", "process_notification_job", "send_real_email"]
