"""
FastAPI Application Entry Point
Exposes API endpoints to enqueue Celery tasks, poll task status, and check application health.
"""

import os
import re
import logging
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Starting up FastAPI application")
    logger.info(f"Loaded Configuration: {settings.safe_dict()}")
    yield
    # Shutdown sequence
    logger.info("Shutting down FastAPI application")


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

    try:
        task = write_log_celery.delay(f"Notification sent to {clean_email}")
        logger.info(f"Enqueued task {task.id} for email: {clean_email}")
        return {
            "message": f"Email will be sent to {clean_email}",
            "task_id": task.id,
        }
    except Exception as exc:
        logger.error(f"Failed to enqueue task to broker: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message broker unavailable. Background task could not be queued.",
        )


@app.get("/task_status/{task_id}", status_code=status.HTTP_200_OK, tags=["Tasks"])
async def get_task_status(task_id: str):
    """
    Endpoint to check the status and result of a background Celery task.
    Uses AsyncResult bound explicitly to our Celery instance.
    """
    if not task_id or not task_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task_id cannot be empty")

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