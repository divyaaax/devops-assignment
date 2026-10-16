"""
Local Development Stack Launcher
Launches:
1. Embedded Redis Server on 127.0.0.1:6379
2. Celery Worker daemon process
3. FastAPI Backend with Uvicorn on http://127.0.0.1:8000
Allows running and demonstrating the complete application locally without Docker or external Redis installed!
"""

import sys
import os
import time
import subprocess
import threading
import logging
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(name)s] %(message)s")
logger = logging.getLogger("stack_runner")

def start_redis_server():
    """Starts pure-Python embedded Redis server on 127.0.0.1:6379."""
    from fakeredis import TcpFakeServer
    logger.info("Initializing Local Redis on 127.0.0.1:6379...")
    server = TcpFakeServer(("127.0.0.1", 6379))
    server.serve_forever()

def main():
    logger.info("=" * 60)
    logger.info("Starting Complete DevOps Application Stack")
    logger.info("=" * 60)

    # 1. Start Redis in background thread
    redis_thread = threading.Thread(target=start_redis_server, daemon=True)
    redis_thread.start()
    time.sleep(1)

    # Verify Redis
    import redis
    r = redis.Redis(host="127.0.0.1", port=6379)
    try:
        if r.ping():
            logger.info("Local Redis server is ready on 127.0.0.1:6379.")
    except Exception as e:
        logger.error(f"Redis startup failed: {e}")
        sys.exit(1)

    # 2. Start Celery Worker process
    python_exe = sys.executable
    worker_cmd = [
        python_exe,
        "-m",
        "celery",
        "-A",
        "worker.celery",
        "worker",
        "--loglevel=info",
        "--pool=solo",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir)
    env["REDIS_HOST"] = "localhost"
    env["REDIS_PORT"] = "6379"

    logger.info("Spawning Celery Worker process...")
    worker_proc = subprocess.Popen(worker_cmd, cwd=str(backend_dir), env=env)

    # 3. Start FastAPI Uvicorn
    import uvicorn
    logger.info("FastAPI starting on http://127.0.0.1:8000 (Open in browser!)")
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", app_dir=str(backend_dir))
    except KeyboardInterrupt:
        logger.info("Stopping stack...")
    finally:
        worker_proc.terminate()
        worker_proc.wait()
        logger.info("Stack shut down successfully.")

if __name__ == "__main__":
    main()
