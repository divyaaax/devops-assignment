# Engineering Journey & Technical Architecture Decisions

This document chronicles the real-world engineering journey of analyzing the starter repository, identifying architectural deficiencies and security vulnerabilities, redesigning the system for containerization and cloud deployment, and implementing a production-grade DevOps solution.

---

## 1. Initial Repository Analysis & Discovery

Upon cloning and inspecting the source repository, we discovered a bare-bones proof of concept with severe operational and security flaws:

### Initial Repository Inventory
- `backend/main.py`: FastAPI service with 3 routes (`POST /notify/`, `GET /task_status/{task_id}`, `POST /health/`).
- `backend/worker.py`: Celery worker configured with static local Redis connection strings.
- `frontend/index.html`: Single-page vanilla JavaScript client with hardcoded `API_BASE = "http://localhost:8000"`.
- `requirements.txt`: 4 unpinned dependencies (`fastapi`, `uvicorn`, `celery`, `redis`).
- `.gitignore`: Contained only `venv`, lacking ignores for Python cache, `.env` files, or Terraform state.
- `journey.md`: Placeholder file containing 1 line (`### Fill Complete Journey`).

### Critical Problems & Gaps Identified
1. **Hardcoded Connection Strings**: `worker.py` hardcoded `broker="redis://localhost:6379/0"` and `backend="redis://localhost:6379/0"`. When placed in separate containers or in AWS, `localhost` fails immediately because containers have isolated network namespaces.
2. **Missing Celery Binding in `AsyncResult`**: In `main.py`, `AsyncResult(task_id)` was called without specifying `app=celery`. In multi-process or cloud setups, Celery defaults to an unconfigured fallback app, leading to state lookup failures.
3. **Flawed Healthcheck Verb**: The health check endpoint was defined as `@app.post("/health/")`. Standard AWS Application Load Balancer target group probes and container health checks send HTTP `GET /health`. Probing a POST-only endpoint returns `405 Method Not Allowed`, marking the service perpetually unhealthy!
4. **Permissive CORS & Credentials**: `CORSMiddleware` had `allow_origins=["*"]` combined with `allow_credentials=True`. Standard browser security specifications reject wildcard origins when credentials are true.
5. **No Email Input Validation**: An invalid email or empty string passed to `POST /notify/?email=` would be accepted, creating orphan background tasks.
6. **No Containerization**: No `Dockerfile` or `docker-compose.yml` existed.
7. **No Infrastructure as Code (IaC)**: Zero cloud resource definitions.
8. **No Automated Testing or CI/CD**: No tests existed to verify functionality or regressions.

---

## 2. Core Architectural & Design Decisions

### A. Container Architecture: Shared Base vs. Separate Images
- **Decision**: We created distinct `Dockerfile.backend` and `Dockerfile.worker` definitions utilizing multi-stage builds.
- **Rationale**:
  - While both services share the Python runtime and dependencies, separating their Dockerfiles allows independent container lifecycle management, distinct container `HEALTHCHECK` probes, and minimal runtime footprints.
  - The backend runs Uvicorn on port 8000; the worker runs Celery with concurrency controls and zero open ports.
  - Both run as an unprivileged system user (`appuser`, UID 10001) for container security.

### B. Local Orchestration: Docker Compose
- **Decision**: Implemented `docker-compose.yml` orchestrating `backend`, `worker`, and `redis`.
- **Rationale**: Docker Compose provides developer parity with cloud networking. Using a bridge network `devops-network`, services communicate via DNS names (`redis`), eliminating `localhost` dependencies. Service startup ordering is guaranteed using `condition: service_healthy`.

### C. Cloud Compute: AWS ECS Fargate
- **Decision**: Chose Amazon Elastic Container Service (ECS) with the AWS Fargate launch type over self-hosted EC2 or Kubernetes (EKS).
- **Rationale**:
  - Fargate removes the operational overhead of provisioning, patching, and scaling EC2 instances.
  - Unlike Kubernetes, which introduces steep complexity (control plane costs, ingress controllers, CNI, Helm), ECS Fargate is lightweight, cost-effective for microservices, and integrates natively with AWS Application Load Balancers and CloudWatch.

### D. Managed Cache: Amazon ElastiCache for Redis
- **Decision**: Preferred AWS ElastiCache for Redis over running Redis in an ECS container in production.
- **Rationale**:
  - Redis in production requires automated backups, high availability failover, in-transit encryption (TLS), at-rest encryption, and automated maintenance windows. ElastiCache provides these natively with AWS SLA guarantees.
  - For assessment cost control, we configured a single-node `cache.t4g.micro` Graviton2 instance (~$0.016/hr) placed strictly inside private subnets with no public internet ingress.

### E. Infrastructure as Code: Terraform
- **Decision**: Built modular, reusable Terraform configurations (`networking`, `ecr`, `load_balancer`, `redis`, `ecs`, `monitoring`).
- **Rationale**: Declarative IaC ensures 100% reproducible environments. Separate modules isolate failure domains and enable clean parameterization across `dev`, `staging`, and `production`.

### F. CI/CD Authentication: GitHub Actions OIDC
- **Decision**: Used GitHub OpenID Connect (OIDC) with AWS IAM instead of static, long-lived AWS IAM User Access Keys.
- **Rationale**:
  - Long-lived keys stored in GitHub Secrets are a primary vector for cloud credential compromise.
  - With OIDC, GitHub Actions exchanges short-lived JSON Web Tokens (JWT) for temporary STS credentials via `AssumeRoleWithWebIdentity`, scoped strictly to the repository and branch.

---

## 3. Real Challenges Encountered & Verified Solutions

### Challenge 1: Celery Task `bind=True` Signature Mismatch in Unit Tests
- **Symptom**: During initial `pytest` execution, `test_write_log_celery_execution` failed with:
  `TypeError: write_log_celery() takes 2 positional arguments but 3 were given`.
- **Root Cause**: The Celery task was declared with `@celery.task(bind=True)`. When calling the task function directly in Python, Celery's `__call__` wrapper automatically injects `self` as the first argument. Passing `mock_self` manually injected an extra argument.
- **Solution**: Refactored the test to use Celery's native `.apply(args=[...])` execution pattern:
  `result = write_log_celery.apply(args=["Notification sent to test@example.com"]).get()`.
- **Verified Outcome**: `test_worker.py` passed immediately with full log file assertion.

### Challenge 2: FastAPI Deprecation Warning on `@app.on_event("startup")`
- **Symptom**: Running pytest generated deprecation warnings:
  `DeprecationWarning: on_event is deprecated, use lifespan event handlers instead`.
- **Solution**: Replaced the legacy `@app.on_event("startup")` handler in `backend/main.py` with the modern `contextlib.asynccontextmanager` `lifespan` handler.
- **Verified Outcome**: Zero deprecation warnings on application lifecycle events.

### Challenge 3: Cost Optimization vs. Cloud Connectivity (NAT Gateway)
- **Symptom**: Standard AWS best practices place ECS tasks in private subnets with an AWS NAT Gateway for outbound ECR pulls and CloudWatch logging. However, an AWS NAT Gateway costs ~$35/month even when idle, which is wasteful for an assessment demo.
- **Solution**: Engineered a modular boolean flag `enable_nat_gateway = false` in Terraform:
  - When `false` (default dev assessment): ECS tasks are deployed in public subnets with public IP assigned (`assign_public_ip = true`). Inbound traffic is still strictly blocked by Security Groups (Backend accepts only ALB on 8000; Worker accepts zero inbound).
  - When `true` (enterprise production): ECS tasks are placed in private subnets behind a NAT Gateway with `assign_public_ip = false`.
- **Verified Outcome**: Flexible architecture that saves cloud costs while retaining enterprise production topology.

---

## 4. Verification and Testing Status

| Component / Layer | Status | Validation Method & Evidence |
| :--- | :--- | :--- |
| **Backend Configuration** | Locally Tested & Verified | 4 tests in `test_config.py` passed (defaults, CORS parsing, SSL URL generation, secret masking). |
| **Health Endpoints** | Locally Tested & Verified | 3 tests in `test_health.py` passed (GET `/health`, GET `/health/`, POST `/health/`). |
| **API & Task Enqueuing** | Locally Tested & Verified | 7 tests in `test_api.py` passed (valid email 202, invalid email 422, empty email 400, broker down 503, completed, failed, in progress). |
| **Celery Worker Task** | Locally Tested & Verified | `test_worker.py` passed (verified file append and return string format). |
| **Frontend Polling & UX** | Implemented & Verified | Tested client polling, dynamic API resolution, max poll timeout (60s), and error display. |
| **Dockerfiles & Compose** | Implemented & Verified | Validated syntax for multi-stage builds, non-root user (10001), healthchecks, and Compose network bridging. |
| **Terraform Modules** | Implemented & Code-Complete | Complete modules created (`networking`, `ecr`, `load_balancer`, `redis`, `ecs`, `monitoring`, `bootstrap`). |
| **GitHub Actions CI/CD** | Implemented & Code-Complete | `ci.yml` and `deploy.yml` with AWS OIDC, ECR SHA tagging, ECS rollout, and Trivy security scanning. |
| **Live AWS Cloud Rollout** | Unverified / Requires AWS Credentials | Requires live AWS account credentials and OIDC trust setup to provision billable resources. |

---

## 5. Remaining Limitations & Future Improvements
1. **HTTPS / TLS on Custom Domain**: Currently configured for HTTP on port 80 via ALB DNS. For production, register a Route53 domain and attach an AWS Certificate Manager (ACM) certificate to enable HTTPS listener on port 443.
2. **WebSocket / SSE for Status**: The current implementation polls `GET /task_status/{task_id}` every 2 seconds. In higher-throughput systems, Server-Sent Events (SSE) or WebSockets would eliminate HTTP polling overhead.
3. **Dead Letter Queue (DLQ)**: In production, configure Celery and Redis with a dead-letter exchange to capture repeatedly failing background tasks for manual inspection.