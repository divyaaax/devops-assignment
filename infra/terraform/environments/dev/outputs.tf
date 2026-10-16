# ==============================================================================
# Development Environment Outputs
# Exposes critical infrastructure identifiers for operations, CI/CD, and access
# ==============================================================================

output "application_url" {
  value       = "http://${module.load_balancer.alb_dns_name}"
  description = "Public HTTP URL to access the FastAPI backend application via ALB"
}

output "alb_dns_name" {
  value       = module.load_balancer.alb_dns_name
  description = "Application Load Balancer DNS hostname"
}

output "ecr_backend_repository_url" {
  value       = module.ecr.backend_repository_url
  description = "Amazon ECR repository URI for backend Docker images"
}

output "ecr_worker_repository_url" {
  value       = module.ecr.worker_repository_url
  description = "Amazon ECR repository URI for worker Docker images"
}

output "ecs_cluster_name" {
  value       = module.ecs.cluster_name
  description = "Amazon ECS Cluster Name"
}

output "ecs_backend_service_name" {
  value       = module.ecs.backend_service_name
  description = "Backend ECS Service Name"
}

output "ecs_worker_service_name" {
  value       = module.ecs.worker_service_name
  description = "Worker ECS Service Name"
}

output "redis_endpoint" {
  value       = module.redis.redis_endpoint
  description = "Primary ElastiCache Redis endpoint hostname (credentials sanitized)"
}

output "backend_log_group" {
  value       = module.ecs.backend_log_group_name
  description = "CloudWatch log group for backend container logs"
}

output "worker_log_group" {
  value       = module.ecs.worker_log_group_name
  description = "CloudWatch log group for worker container logs"
}
