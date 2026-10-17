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


def send_via_resend(recipient_email: str, task_id: str, api_key: str) -> str:
    """Delivers real email via Resend HTTPS API (Port 443), works on Render Free Tier without SMTP blocks."""
    import json
    import urllib.request
    import urllib.error

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "User-Agent": "DevOps-Assessment/1.0",
    }
    payload = {
        "from": "DevOps Task Notifier <onboarding@resend.dev>",
        "to": [recipient_email.strip()],
        "subject": "DevOps Assessment: Real-Time Task Notification",
        "text": (
            f"Hello,\n\n"
            f"This is a verified real-time notification sent from your containerized "
            f"FastAPI + Celery + Redis application stack on Render.\n\n"
            f"Task Details:\n"
            f"- Task ID: {task_id}\n"
            f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
            f"- Status: Successfully processed by Celery worker pool\n"
            f"- Protocol: HTTPS Port 443 (Render-Compatible)\n\n"
            f"Best regards,\n"
            f"DevOps Assessment Application"
        ),
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            logger.info(f"Real email successfully dispatched to {recipient_email} via Resend HTTPS API")
            return f"Real email dispatched to {recipient_email} via Resend API"
    except urllib.error.HTTPError as http_err:
        err_body = http_err.read().decode("utf-8", errors="replace")
        logger.error(f"Resend API error HTTP {http_err.code}: {err_body}")
        raise RuntimeError(f"Resend API HTTP {http_err.code}: {err_body}") from http_err


def send_real_email(recipient_email: str, task_id: str) -> str:
    """Sends a real email using configured provider (Resend HTTPS API or Gmail SMTP)."""
    # 1. Prefer Resend API if configured (port 443 HTTPS, bypasses Render SMTP firewall)
    resend_key = os.environ.get("RESEND_API_KEY") or getattr(settings, "RESEND_API_KEY", None)
    if resend_key and resend_key.strip():
        return send_via_resend(recipient_email, task_id, resend_key.strip())

    # 2. Standard Gmail / Custom SMTP
    smtp_user = (settings.SMTP_USER or "").replace('"', "").replace("'", "").strip()
    smtp_password = (settings.SMTP_PASSWORD or "").replace(" ", "").replace('"', "").replace("'", "").strip()

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD (or RESEND_API_KEY) must be configured for real email delivery")

    from_addr = (settings.SMTP_FROM or smtp_user).replace('"', "").replace("'", "").strip()
    recipient_email = recipient_email.strip()

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
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    logger.info(f"Real email successfully dispatched to {recipient_email}")
    return f"Real email dispatched to {recipient_email}"


def process_notification_job(task_id: str, message: str) -> str:
    """
    Core notification execution logic:
    1. Simulates or delivers real email via Gmail SMTP if configured.
    2. Writes local log file.
    3. Returns status message for client UI.
    """
    logger.info(f"Task started (ID: {task_id}): {message}")

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
            raise RuntimeError(f"SMTP Delivery Failed: {str(exc)}") from exc
    else:
        # Standard simulated duration
        duration = settings.TASK_SIMULATION_SECONDS
        if duration > 0:
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


@celery.task(bind=True, name="worker.write_log_celery")
def write_log_celery(self, message: str):
    task_id = self.request.id or "standalone-task"
    return process_notification_job(task_id, message)
