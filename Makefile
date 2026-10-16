.PHONY: help build up down logs logs-backend logs-worker logs-redis test clean tf-init tf-plan

help:
	@echo "DevOps Assessment Task Runner"
	@echo "--------------------------------------------------------"
	@echo "make build         : Build all Docker container images"
	@echo "make up            : Start the full stack locally with Docker Compose"
	@echo "make down          : Stop all containers and preserve volumes"
	@echo "make clean         : Stop containers and remove volumes and orphans"
	@echo "make logs          : Follow unified logs of all running services"
	@echo "make logs-backend  : Follow FastAPI backend container logs"
	@echo "make logs-worker   : Follow Celery worker container logs"
	@echo "make logs-redis    : Follow Redis container logs"
	@echo "make test          : Run Python unit & integration test suite"
	@echo "make tf-init       : Initialize Terraform dev environment"
	@echo "make tf-plan       : Generate Terraform infrastructure plan"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

clean:
	docker compose down -v --remove-orphans

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-worker:
	docker compose logs -f worker

logs-redis:
	docker compose logs -f redis

test:
	pytest -v backend/tests

tf-init:
	cd infra/terraform/environments/dev && terraform init

tf-plan:
	cd infra/terraform/environments/dev && terraform plan
