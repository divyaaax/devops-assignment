output "backend_repository_url" {
  value       = aws_ecr_repository.backend.repository_url
  description = "ECR Repository URL for backend container images"
}

output "backend_repository_arn" {
  value       = aws_ecr_repository.backend.arn
  description = "ECR Repository ARN for backend"
}

output "worker_repository_url" {
  value       = aws_ecr_repository.worker.repository_url
  description = "ECR Repository URL for worker container images"
}

output "worker_repository_arn" {
  value       = aws_ecr_repository.worker.arn
  description = "ECR Repository ARN for worker"
}
