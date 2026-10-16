output "vpc_id" {
  value       = aws_vpc.main.id
  description = "The ID of the VPC"
}

output "public_subnet_ids" {
  value       = aws_subnet.public[*].id
  description = "List of IDs of public subnets"
}

output "private_subnet_ids" {
  value       = aws_subnet.private[*].id
  description = "List of IDs of private subnets"
}

output "alb_security_group_id" {
  value       = aws_security_group.alb.id
  description = "Security Group ID for the ALB"
}

output "ecs_backend_security_group_id" {
  value       = aws_security_group.ecs_backend.id
  description = "Security Group ID for the ECS backend tasks"
}

output "ecs_worker_security_group_id" {
  value       = aws_security_group.ecs_worker.id
  description = "Security Group ID for the ECS worker tasks"
}

output "redis_security_group_id" {
  value       = aws_security_group.redis.id
  description = "Security Group ID for ElastiCache Redis"
}
