# System Architecture & Cloud Infrastructure

This document outlines both the **CI/CD Deployment Architecture** and the **AWS Runtime Cloud Architecture** for the containerized application.

---

## 1. CI/CD Deployment Architecture

The following diagram illustrates the automated deployment pipeline from local code commit through GitHub Actions, AWS OIDC authentication, Amazon ECR image registry, and Amazon ECS Fargate deployment:

```mermaid
flowchart TD
    subgraph Developer_Workstation ["Developer Workstation"]
        Dev["fa:fa-user Developer"]
        GitCommit["git commit & git push main"]
    end

    subgraph GitHub ["GitHub Platform"]
        Repo["GitHub Repository\n(devops-assignment)"]
        
        subgraph GHA_CI ["CI Workflow (ci.yml)"]
            LintStep["1. Flake8 Linting & Code Quality"]
            TestStep["2. Pytest Test Suite & Coverage"]
            BuildStep["3. Docker Image Build (Backend & Worker)"]
            TrivyScan["4. Trivy Container Vulnerability Scan"]
        end

        subgraph GHA_CD ["CD Workflow (deploy.yml)"]
            OIDC_Request["1. Request JWT ID Token"]
            ECR_Login["2. ECR Authentication"]
            Image_Push["3. Tag with Commit SHA & Push Images"]
            Deploy_ECS["4. Update Task Defs & Rollout ECS Services"]
            Health_Check["5. Verify Endpoint via ALB /health"]
        end
    end

    subgraph AWS_Cloud ["Amazon Web Services (AWS)"]
        IAM_OIDC["IAM Identity Provider\n(token.actions.githubusercontent.com)"]
        DeployRole["IAM Deployment Role\n(AssumeRoleWithWebIdentity)"]
        
        subgraph ECR ["Amazon Elastic Container Registry (ECR)"]
            ECR_Backend["ECR: devops-assessment-backend\n(:sha-xyz & :latest)"]
            ECR_Worker["ECR: devops-assessment-worker\n(:sha-xyz & :latest)"]
        end

        subgraph ECS_Cluster ["Amazon ECS Fargate Cluster"]
            ECS_Backend_Service["ECS Service: backend-service"]
            ECS_Worker_Service["ECS Service: worker-service"]
        end
    end

    Dev --> GitCommit --> Repo
    Repo --> GHA_CI
    LintStep --> TestStep --> BuildStep --> TrivyScan
    TrivyScan -->|On Success & Push to Main| GHA_CD

    OIDC_Request <-->|Exchange JWT for Temp Credentials| IAM_OIDC
    IAM_OIDC --> DeployRole
    DeployRole --> ECR_Login
    ECR_Login --> Image_Push
    Image_Push --> ECR_Backend
    Image_Push --> ECR_Worker
    Deploy_ECS --> ECS_Backend_Service
    Deploy_ECS --> ECS_Worker_Service
    Health_Check -->|Verify HTTP 200| ECS_Backend_Service
```

---

## 2. AWS Runtime Cloud Architecture

The following diagram depicts the AWS cloud architecture, isolating services across public and private subnets, security groups, load balancing, message queuing, and CloudWatch monitoring:

```mermaid
flowchart TB
    subgraph Users ["External Traffic"]
        Browser["User Web Browser\n(Desktop / Mobile)"]
    end

    subgraph AWS ["Amazon Web Services (AWS) - us-east-1"]
        
        subgraph VPC ["AWS Virtual Private Cloud (10.0.0.0/16)"]
            IGW["Internet Gateway"]

            subgraph Public_Subnets ["Public Subnets (us-east-1a, us-east-1b)"]
                ALB["Application Load Balancer (ALB)\n(Port 80 / 443)\nSG: alb-sg (0.0.0.0/0)"]
            end

            subgraph Task_Subnets ["Application Tier (ECS Fargate)"]
                direction TB
                
                subgraph Backend_Group ["FastAPI Backend Container"]
                    Backend["FastAPI App (Port 8000)\nNon-root user (appuser)\nSG: ecs-backend-sg\n(Ingress: Port 8000 from alb-sg only)"]
                end

                subgraph Worker_Group ["Celery Worker Container"]
                    Worker["Celery Asynchronous Worker\nNon-root user (appuser)\nSG: ecs-worker-sg\n(Zero Inbound Ports Allowed)"]
                end
            end

            subgraph Private_Data_Subnets ["Data Tier (Isolated Private Subnets)"]
                Redis["Amazon ElastiCache for Redis 7.x\n(Port 6379, Encryption at Rest)\nSG: redis-sg\n(Ingress: Port 6379 from ecs-backend-sg & ecs-worker-sg only)"]
            end
        end

        subgraph Observability ["Observability & IAM"]
            CW_Logs["Amazon CloudWatch Logs\n(/ecs/backend & /ecs/worker)\nRetention: 7 Days"]
            CW_Alarms["CloudWatch Alarms\n- CPU/Memory > 80%\n- ALB Unhealthy Hosts > 0\n- ALB 5XX Rate > 5"]
            IAM_Execution["ECS Task Execution Role\n(ECR Pull, CloudWatch Write)"]
            IAM_Task["ECS Task Workload Role"]
        end
    end

    %% External routing
    Browser -->|HTTP Request| IGW
    IGW -->|Forward| ALB
    ALB -->|Forward :8000| Backend

    %% Application task flow
    Backend -->|1. Enqueue Task\nwrite_log_celery.delay| Redis
    Backend -->|Return task_id| ALB
    ALB -->|Return 202 Accepted| Browser

    Worker -->|2. Prefetch Task from Queue| Redis
    Worker -->|3. Execute 6s Simulation & Append Log| Worker
    Worker -->|4. Store Result in Backend| Redis

    Browser -.->|5. Poll GET /task_status/task_id| ALB
    ALB -.-> Backend
    Backend -.->|6. Query AsyncResult| Redis
    Redis -.->|7. Return State: completed| Backend
    Backend -.->|8. Return Status JSON| Browser

    %% Logging and IAM
    Backend -.->|Container Logs| CW_Logs
    Worker -.->|Worker Logs| CW_Logs
    ALB -.->|Metrics| CW_Alarms
    Backend -.->|Metrics| CW_Alarms
    IAM_Execution -.-> Backend
    IAM_Execution -.-> Worker
```

---

## 3. Distributed Task Lifecycle Journey

1. **User Action**: The client triggers the notification form in `frontend/index.html`.
2. **FastAPI Request**: The browser submits `POST /notify/?email=user@example.com` to the Application Load Balancer, which routes to the backend on port 8000.
3. **Queue Enqueue**: FastAPI invokes `write_log_celery.delay()`. Celery serializes the task into Redis queue `celery`.
4. **Immediate Response**: FastAPI immediately returns HTTP 202 Accepted: `{"message": "Email will be sent to...", "task_id": "<uuid>"}` without blocking.
5. **Worker Pickup**: The headless Celery worker polls Redis, claims the job, and updates task state to `STARTED`.
6. **Execution**: The worker simulates background work, writes the audit log, and finishes.
7. **Result Persistence**: Celery stores the result string (`Task completed: ...`) in Redis key `celery-task-meta-<uuid>`.
8. **Client Polling**: The frontend periodically queries `GET /task_status/<uuid>` every 2 seconds.
9. **Result Return**: FastAPI queries `AsyncResult(task_id, app=celery)`. Once `ready()` is true, it returns `status: "completed"` and the result string.
10. **UI Update**: The frontend displays the completed state, stops polling, and updates the progress indicator.
