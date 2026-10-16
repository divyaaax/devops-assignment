"""
Celery Worker Application
Executes asynchronous background tasks with logging, file tracking, and real SMTP email delivery.
"""

import os
import re
import time
import logging
import smtplib
from email.message import EmailMessage
from celery import Celery
from config import settings

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("celery_worker")

# Configure Celery with environment-derived broker and result backend URLs
celery = Celery(
    "worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend_url,
)

celery.conf.update(
    task_track_started=True,
    result_extended=True,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

logger.info(f"Celery worker configured. Broker: {settings.safe_dict()['CELERY_BROKER_MASKED']}")


def send_real_email(recipient_email: str, task_id: str) -> str:
    """Sends a real email using configured SMTP provider (e.g. Gmail SMTP)."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise ValueError("SMTP_USER and SMTP_PASSWORD must be configured in .env for real email delivery")

    from_addr = settings.SMTP_FROM or settings.SMTP_USER
    msg = EmailMessage()
    msg["Subject"] = "DevOps Assessment: Real-Time Task Notification"
    msg["From"] = from_addr
    msg["To"] = recipient_email
    msg.set_content(
        f"Hello,\n\n"
        f"This is a verified real-time notification sent from your containerized "
        f"FastAPI + Celery + Redis application stack.\n\n"
        f"Task Details:\n"
        f"- Task ID: {task_id}\n"
        f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
        f"- Status: Successfully processed by Celery worker pool\n"
        f"- Message Broker: Redis\n\n"
        f"Best regards,\n"
        f"DevOps Assessment Application"
    )

    logger.info(f"Connecting to SMTP server {settings.SMTP_HOST}:{settings.SMTP_PORT} for {recipient_email}...")
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
    logger.info(f"Real email successfully dispatched to {recipient_email}")
    return f"Real email dispatched to {recipient_email}"


@celery.task(bind=True, name="worker.write_log_celery")
def write_log_celery(self, message: str):
    """
    Processes notification task:
    1. Simulates or delivers real email via Gmail SMTP if configured.
    2. Writes local log file.
    3. Returns status message for client UI.
    """
    logger.info(f"Task started (ID: {self.request.id}): {message}")
    task_id = self.request.id or "standalone-task"

    # Extract recipient email address if present in message
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", message)
    recipient = email_match.group(0) if email_match else None

    # Real email delivery if enabled and credentials configured
    if settings.ENABLE_REAL_EMAIL and recipient:
        try:
            send_real_email(recipient, task_id)
            result_message = f"Task completed (Real email sent to {recipient}): {message}"
        except Exception as exc:
            logger.error(f"Failed to deliver real email via SMTP: {exc}", exc_info=True)
            result_message = f"Task completed (SMTP Error: {str(exc)}): {message}"
    else:
        # Standard simulated duration
        duration = settings.TASK_SIMULATION_SECONDS
        time.sleep(duration)
        result_message = f"Task completed: {message}"

    # Write log file safely
    log_file_path = os.getenv("CELERY_LOG_FILE", "log_celery.txt")
    if log_file_path:
        try:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {result_message}\n")
        except Exception as e:
            logger.warning(f"Could not write to local log file: {e}")

    logger.info(f"Task completed successfully (ID: {task_id}): {result_message}")
    return result_message
