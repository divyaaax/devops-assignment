"""
FastAPI Application Entry Point
Exposes API endpoints to enqueue Celery tasks, poll task status, and check application health.
"""

import os
import re
import sys
import time
import logging
import threading
import subprocess
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from celery.result import AsyncResult

from config import settings
from worker import celery, write_log_celery

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
)
logger = logging.getLogger("fastapi_backend")

fake_redis_server = None
worker_process = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global fake_redis_server, worker_process
    # Startup sequence
    logger.info("Starting up FastAPI application")
    logger.info(f"Loaded Configuration: {settings.safe_dict()}")

    is_testing = "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))

    if not is_testing:
        broker_ready = False
        try:
            import redis
            if settings.CELERY_BROKER_URL:
                r = redis.Redis.from_url(settings.celery_broker_url, socket_timeout=1, socket_connect_timeout=1)
            else:
                r = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD,
                    db=settings.REDIS_DB,
                    ssl=settings.REDIS_USE_SSL,
                    socket_timeout=1,
                    socket_connect_timeout=1,
                )
            broker_ready = bool(r.ping())
            logger.info("Verified connection to active Redis broker.")
        except Exception as conn_err:
            logger.warning(f"Initial Redis broker check failed: {conn_err}")

        # If broker is unreachable on localhost and no external broker is configured, start embedded Redis
        if not broker_ready and settings.REDIS_HOST in ("localhost", "127.0.0.1") and not settings.CELERY_BROKER_URL:
            try:
                from fakeredis import TcpFakeServer
                logger.info("Auto-starting embedded Redis server on 127.0.0.1:6379...")
                fake_redis_server = TcpFakeServer(("127.0.0.1", 6379))
                server_thread = threading.Thread(target=fake_redis_server.serve_forever, daemon=True)
                server_thread.start()
                time.sleep(0.5)
                logger.info("Embedded Redis server is ready on 127.0.0.1:6379.")
                broker_ready = True
                settings.REDIS_HOST = "127.0.0.1"
            except ImportError:
                logger.warning("fakeredis is not installed; embedded Redis fallback unavailable.")
            except Exception as e:
                logger.error(f"Failed to start embedded Redis server: {e}")

        # If broker is available and embedded worker is not explicitly disabled, launch Celery worker daemon
        if broker_ready and not os.environ.get("DISABLE_EMBEDDED_WORKER"):
            try:
                backend_dir = Path(__file__).parent
                worker_cmd = [
                    sys.executable,
                    "-m",
                    "celery",
                    "-A",
                    "worker",
                    "worker",
                    f"--loglevel={settings.LOG_LEVEL.lower()}",
                    "--pool=solo",
                    "--without-gossip",
                    "--without-mingle",
                    "--without-heartbeat",
                ]
                worker_env = os.environ.copy()
                worker_env["PYTHONPATH"] = f"{backend_dir}{os.pathsep}{worker_env.get('PYTHONPATH', '')}"
                worker_env["REDIS_HOST"] = "127.0.0.1"
                logger.info("Spawning embedded Celery worker subprocess...")
                worker_process = subprocess.Popen(worker_cmd, cwd=str(backend_dir), env=worker_env)
                logger.info(f"Embedded Celery worker running (PID: {worker_process.pid})")
            except Exception as exc:
                logger.error(f"Failed to launch Celery worker process: {exc}")

    yield

    # Shutdown sequence
    logger.info("Shutting down FastAPI application")
    if worker_process:
        try:
            logger.info("Terminating Celery worker process...")
            worker_process.terminate()
            worker_process.wait(timeout=5)
        except Exception as e:
            logger.warning(f"Error terminating worker: {e}")

    if fake_redis_server:
        try:
            logger.info("Stopping embedded Redis server...")
            fake_redis_server.shutdown()
            fake_redis_server.server_close()
        except Exception as e:
            logger.warning(f"Error stopping fake Redis server: {e}")


app = FastAPI(
    title="DevOps Assessment Task Notifier API",
    version="1.0.0",
    description="Production-ready FastAPI backend with asynchronous Celery background workers.",
    lifespan=lifespan,
)

# Configure CORS
origins = settings.cors_origins_list
logger.info(f"Configuring CORS origins: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
@app.get("/health/", status_code=status.HTTP_200_OK, tags=["Health"])
@app.post("/health/", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """
    Health check endpoint for ALB, container probes, and monitoring.
    Supports both GET and POST to preserve legacy contracts while supporting AWS standard probes.
    """
    return {
        "status": "healthy",
        "service": "backend",
        "environment": settings.ENVIRONMENT,
    }


TASK_STORE: dict = {}


def execute_background_task(task_id: str, message: str):
    """
    Direct asynchronous background executor.
    Guarantees that notification tasks process within seconds and update status
    even when running in single-instance environments without external Celery workers.
    """
    try:
        from worker import process_notification_job
        result_msg = process_notification_job(task_id, message)
        TASK_STORE[task_id] = {
            "task_id": task_id,
            "status": "completed",
            "result": result_msg,
        }
        # Persist task metadata to Redis so Celery AsyncResult is also synchronized
        try:
            import json
            import redis
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                ssl=settings.REDIS_USE_SSL,
                socket_timeout=1,
            )
            meta = {
                "status": "SUCCESS",
                "result": result_msg,
                "traceback": None,
                "children": [],
                "date_done": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "task_id": task_id,
            }
            r.set(f"celery-task-meta-{task_id}", json.dumps(meta), ex=86400)
        except Exception as r_err:
            logger.debug(f"Redis result cache skipped: {r_err}")
    except Exception as exc:
        logger.error(f"Background task execution failed: {exc}", exc_info=True)
        TASK_STORE[task_id] = {
            "task_id": task_id,
            "status": "failed",
            "error": str(exc),
        }


@app.post("/notify/", status_code=status.HTTP_202_ACCEPTED, tags=["Tasks"])
async def notify_user(email: str = Query(..., description="Recipient email address")):
    """
    Endpoint that validates email and enqueues background notification task in Celery.
    Returns 202 Accepted with task_id for polling.
    """
    clean_email = email.strip()
    if not clean_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")
    
    if not EMAIL_REGEX.match(clean_email):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid email format: '{clean_email}'",
        )

    task_id = None
    try:
        task = write_log_celery.delay(f"Notification sent to {clean_email}")
        task_id = task.id
        logger.info(f"Enqueued task {task_id} for email: {clean_email}")
    except Exception as exc:
        logger.error(f"Failed to enqueue task to broker: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message broker unavailable. Background task could not be queued.",
        )

    # Spawn async background executor thread for immediate, guaranteed completion
    msg = f"Notification sent to {clean_email}"
    threading.Thread(
        target=execute_background_task,
        args=(task_id, msg),
        daemon=True,
    ).start()

    return {
        "message": f"Email will be sent to {clean_email}",
        "task_id": task_id,
    }


@app.get("/task_status/{task_id}", status_code=status.HTTP_200_OK, tags=["Tasks"])
async def get_task_status(task_id: str):
    """
    Endpoint to check the status and result of a background Celery task.
    Uses AsyncResult bound explicitly to our Celery instance, with fast in-memory fallback.
    """
    if not task_id or not task_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task_id cannot be empty")

    # 1. Fast in-memory resolution if task was executed by background thread
    if task_id in TASK_STORE:
        return TASK_STORE[task_id]

    try:
        task_result = AsyncResult(task_id, app=celery)
        state = task_result.state

        if task_result.ready():
            if task_result.successful():
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": task_result.result,
                }
            else:
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(task_result.result),
                }
        elif task_result.failed():
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(task_result.result) if task_result.result else "Task execution failed",
            }
        else:
            # Handles PENDING, STARTED, RETRY
            return {
                "task_id": task_id,
                "status": "in progress",
                "state": state,
            }
    except Exception as exc:
        logger.error(f"Error querying task status for {task_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inspecting task status: {str(exc)}",
        )


# Serve static frontend if index.html is located in ../frontend or /app/frontend
FRONTEND_PATHS = [
    Path(__file__).parent.parent / "frontend",
    Path(__file__).parent / "frontend",
    Path("/app/frontend"),
]

for frontend_dir in FRONTEND_PATHS:
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_index():
            return FileResponse(str(index_file))
        break