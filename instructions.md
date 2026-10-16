# Beginner-Friendly Local Development & Operations Guide

Welcome! This guide provides step-by-step instructions for running, testing, and debugging the containerized FastAPI + Celery + Redis stack on your local machine.

Both **Linux / macOS (Bash)** and **Windows (PowerShell)** commands are provided wherever syntax differs.

---

## 1. Prerequisites
Ensure you have the following installed on your workstation:
- **Git**: [git-scm.com](https://git-scm.com/)
- **Docker & Docker Compose**: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (ensure Docker daemon is running)
- **Python 3.11+** (optional, for running local unit tests outside Docker)

---

## 2. Clone the Repository

### Linux / macOS / Windows (Git Bash):
```bash
git clone https://github.com/kumarnitesh2000-cardit/devops-assignment.git
cd devops-assignment
```

### Windows (PowerShell):
```powershell
git clone https://github.com/kumarnitesh2000-cardit/devops-assignment.git
cd devops-assignment
```

---

## 3. Create the Local Environment Configuration

Copy the template `.env.example` into `.env`:

### Linux / macOS:
```bash
cp .env.example .env
```

### Windows (PowerShell):
```powershell
Copy-Item .env.example .env
```

> **How Docker Networking Works Here**: Inside `docker-compose.yml`, services communicate over a custom bridge network called `devops-network`. The backend and worker containers resolve Redis using the service hostname `redis` (NOT `localhost`). `localhost` only refers to the local container itself.

---

## 4. Build and Start the Full Stack

### Build Images:
```bash
docker compose build
```

### Start Services in Background (-d):
```bash
docker compose up -d
```
*(Or if using Make on Linux/macOS: `make up`)*

### Verify All Containers Are Running and Healthy:
```bash
docker compose ps
```
You should see 3 containers:
- `devops-redis` (Status: `healthy`, port 6379)
- `devops-backend` (Status: `healthy`, port 8000)
- `devops-worker` (Status: `running`)

---

## 5. Test Backend Health Endpoint

### Linux / macOS:
```bash
curl -i http://localhost:8000/health
```

### Windows (PowerShell):
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```
**Expected Response:**
```json
{
  "status": "healthy",
  "service": "backend",
  "environment": "development"
}
```

---

## 6. Access and Test the Frontend

1. Open your web browser and navigate to:
   [http://localhost:8000](http://localhost:8000)
   *(Or open `frontend/index.html` directly in your browser)*
2. In the **Recipient Email** box, enter: `developer@example.com`
3. Click **Send notification**.
4. Observe the real-time UI:
   - A unique **Task ID** appears.
   - Status transitions to **IN PROGRESS**.
   - The worker processes the task (takes ~6 seconds).
   - Status updates to **COMPLETED** with the result:
     `Task completed: Notification sent to developer@example.com`

---

## 7. Inspecting Container Logs in Real Time

### Follow Unified Logs for All Services:
```bash
docker compose logs -f
```

### Follow FastAPI Backend Logs:
```bash
docker compose logs -f backend
```

### Follow Celery Worker Logs:
```bash
docker compose logs -f worker
```

### Follow Redis Logs:
```bash
docker compose logs -f redis
```

---

## 8. Triggering Tasks from Terminal (CLI)

You can also trigger background tasks directly using `curl` or PowerShell:

### Trigger Task:
**Linux / macOS:**
```bash
curl -X POST "http://localhost:8000/notify/?email=tester@example.com"
```

**Windows (PowerShell):**
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/notify/?email=tester@example.com"
```
**Response Output:**
```json
{"message": "Email will be sent to tester@example.com", "task_id": "b3e098a5-dcf4-490b-967a-e4905cfc9b68"}
```

### Check Task Status:
Replace `<task_id>` with the UUID received:

**Linux / macOS:**
```bash
curl "http://localhost:8000/task_status/<task_id>"
```

**Windows (PowerShell):**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/task_status/<task_id>"
```

---

## 9. Troubleshooting & Debugging Guide

### Issue: "Message broker unavailable" (503 Service Unavailable)
- **Cause**: The backend container cannot reach the Redis container on `redis:6379`.
- **Fix**: Verify Redis is healthy:
  ```bash
  docker compose ps redis
  docker compose logs redis
  ```
  Ensure `.env` contains `REDIS_HOST=redis` (when running inside Docker Compose).

### Issue: Celery Worker Not Processing Tasks
- **Cause**: Worker process stopped or failed connecting to Redis.
- **Fix**: Check worker logs:
  ```bash
  docker compose logs worker
  ```
  Restart the worker container:
  ```bash
  docker compose restart worker
  ```

### Issue: Port 8000 or 6379 Already in Use
- **Cause**: Another service (such as local Redis server or another application) is binding port 8000 or 6379.
- **Fix**: Change `BACKEND_PORT=8080` in `.env`, or stop the conflicting local service.

---

## 10. Rebuilding Images After Code Changes

If you modify files in `backend/` or `frontend/`:
```bash
docker compose build --no-cache
docker compose up -d
```

---

## 11. Stopping and Cleaning Up

### Stop Containers (Preserve Data Volume):
```bash
docker compose down
```

### Stop Containers and Purge Volumes & Networks:
```bash
docker compose down -v --remove-orphans
```
*(Or with Make: `make clean`)*

---

## 12. Running Unit Tests Locally

To run the automated `pytest` test suite on your host:

### Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=backend
pytest -v backend/tests
```

### Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH="backend"
pytest -v backend/tests
```
All 15 tests should pass with green status!
