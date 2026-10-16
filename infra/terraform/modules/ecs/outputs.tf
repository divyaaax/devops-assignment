output "cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "Name of the ECS Cluster"
}

output "cluster_arn" {
  value       = aws_ecs_cluster.main.arn
  description = "ARN of the ECS Cluster"
}

output "backend_service_name" {
  value       = aws_ecs_service.backend.name
  description = "Name of the backend ECS service"
}

output "worker_service_name" {
  value       = aws_ecs_service.worker.name
  description = "Name of the worker ECS service"
}

output "backend_log_group_name" {
  value       = aws_cloudwatch_log_group.backend.name
  description = "Name of CloudWatch log group for backend"
}

output "worker_log_group_name" {
  value       = aws_cloudwatch_log_group.worker.name
  description = "Name of CloudWatch log group for worker"
}
