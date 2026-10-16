# DevOps Assessment: Video Walkthrough Script (5–8 Minutes)

This script provides an exact, step-by-step guide for presenting this DevOps assessment in a technical interview or recorded demonstration.

---

## Preparation Checklist
- [ ] Terminal split view (Terminal 1: Commands, Terminal 2: Docker logs)
- [ ] Browser window open to `http://localhost:8000` (or local `frontend/index.html`)
- [ ] VS Code / IDE open to project root showing folder structure
- [ ] AWS Console open (optional if demonstrating live deployed resources)

---

## Presentation Timeline

### 0:00 – 1:00 | Introduction & Architecture Overview
**Screen**: Display [docs/architecture.md](file:///d:/superclaims-devops/docs/architecture.md) Mermaid diagrams.
**Script**:
> "Hello! Today I'm demonstrating our production-ready DevOps implementation for an asynchronous notification application built with FastAPI, Celery, and Redis.
>
> The challenge was taking a basic local prototype with hardcoded parameters and engineering a complete, production-ready solution featuring:
> 1. Multi-stage containerization with non-root privileges and health checks.
> 2. Local orchestration via Docker Compose with health-dependent startup.
> 3. Cloud infrastructure defined declaratively using Terraform on AWS ECS Fargate and ElastiCache.
> 4. Fully automated CI/CD using GitHub Actions with keyless AWS OIDC authentication and vulnerability scanning.
>
> Let's look at how the code is structured."

---

### 1:00 – 2:30 | Containerization & Local Development
**Screen**: Show `Dockerfile.backend`, `Dockerfile.worker`, and `docker-compose.yml`.
**Script**:
> "For containerization, we created separate multi-stage Dockerfiles for the FastAPI backend and Celery worker:
> - Base image is pinned to `python:3.11-slim` for predictable builds and minimal attack surface.
> - A non-root system user (`appuser`, UID 10001) runs all processes to adhere to least-privilege principles.
> - Healthchecks are embedded: `curl` probes `/health` for the backend, while Docker Compose verifies `redis-cli ping` before dependent containers start.
> - Signal handling uses `exec` so SIGTERM is cleanly handled by Uvicorn and Celery for graceful worker shutdown without dropping tasks in flight."

**Terminal Action**:
```bash
# Verify environment setup
cp .env.example .env

# Start stack with Docker Compose
make up
# Or: docker compose up -d

# Verify container health
docker compose ps
```

---

### 2:30 – 3:45 | Live Application Demonstration & Task Lifecycle
**Screen**: Switch to Browser at `http://localhost:8000` (or `frontend/index.html`).
**Terminal 2**: `make logs` or `docker compose logs -f`
**Script**:
> "Now let's demonstrate the end-to-end task lifecycle.
> In the frontend, I enter `dev@example.com` and click 'Send notification'.
>
> Notice what happens:
> 1. FastAPI immediately acknowledges the request with an HTTP 202 Accepted status and returns a unique Task ID.
> 2. The Celery worker picks up the job from the Redis queue. We can see the task execution log appear in our worker logs.
> 3. The frontend polls `GET /task_status/{task_id}` every 2 seconds without overwhelming the server.
> 4. After our worker completes its simulated processing, it writes the result to Redis.
> 5. The UI updates dynamically to 'COMPLETED' and displays the finished message: `Task completed: Notification sent to dev@example.com`."

---

### 3:45 – 5:00 | Automated Testing Suite
**Screen**: Switch to Terminal.
**Script**:
> "Quality assurance is built into every layer. We implemented comprehensive unit and integration tests using `pytest` and FastAPI's `TestClient`. External Celery dependencies and Redis are isolated using mock fixtures so the suite can execute in any clean environment without live AWS connectivity."

**Terminal Action**:
```bash
# Run pytest test suite
make test
# Or: pytest -v backend/tests
```
**Script**:
> "All 15 tests pass in under one second, verifying health endpoints, query validation, edge-case email inputs, task status polling transitions, and configuration masking."

---

### 5:00 – 6:30 | Infrastructure as Code (Terraform)
**Screen**: Open `infra/terraform/`. Show `modules/` and `environments/dev/main.tf`.
**Script**:
> "Our cloud infrastructure is managed entirely with Terraform. It is split into clean, single-responsibility modules:
> - **Networking**: Custom VPC across 2 Availability Zones with public and private subnets. We engineered a cost-optimization toggle (`enable_nat_gateway = false` by default) saving $35/month for assessment testing.
> - **ECR**: Private repositories with automated CVE vulnerability scanning on push and retention policies to expire stale untagged images.
> - **Load Balancer**: Public Application Load Balancer routing to ECS Fargate tasks using IP target groups with health checks against `/health`.
> - **Redis**: Managed Amazon ElastiCache for Redis isolated in private subnets, accessible only from backend and worker security groups.
> - **ECS Fargate**: Serverless container execution with dedicated IAM Execution and Task roles.
> - **Monitoring**: CloudWatch alarms for high CPU, high memory, and ALB target 5xx rates."

**Terminal Action**:
```bash
cd infra/terraform/environments/dev
terraform fmt -check
terraform validate
terraform plan
```

---

### 6:30 – 7:30 | GitHub Actions CI/CD with AWS OIDC
**Screen**: Open `.github/workflows/ci.yml` and `deploy.yml`.
**Script**:
> "Our CI/CD pipeline enforces strict security and automation:
> - **CI (`ci.yml`)**: Triggers on pull requests and commits. It runs flake8 linting, the pytest test suite, builds Docker images, and runs Trivy container vulnerability scanning.
> - **CD (`deploy.yml`)**: Employs **AWS OIDC token exchange** (`AssumeRoleWithWebIdentity`), eliminating the need for long-lived, high-risk AWS Access Keys stored in GitHub Secrets.
> - Images are tagged with immutable Git commit SHAs, pushed to ECR, and rolled out to ECS Fargate services with automatic health verification through the ALB."

---

### 7:30 – 8:00 | Teardown, Cost Considerations & Conclusion
**Screen**: Show `instructions.md` cleanup commands.
**Script**:
> "Finally, cost control is critical in cloud engineering. We've documented clear teardown procedures:
> - Locally: `make clean` or `docker compose down -v` stops containers and purges volumes.
> - On AWS: `terraform destroy` cleanly removes all provisioned cloud infrastructure.
>
> In conclusion, this repository represents a complete, secure, reproducible DevOps solution ready for production evaluation. Thank you!"
