variable "project_name" {
  type        = string
  description = "Project name prefix"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "aws_region" {
  type        = string
  description = "AWS region for CloudWatch logs"
}

variable "backend_image" {
  type        = string
  description = "Docker image URI for backend container"
}

variable "worker_image" {
  type        = string
  description = "Docker image URI for worker container"
}

variable "backend_subnet_ids" {
  type        = list(string)
  description = "Subnet IDs where backend ECS service tasks are placed"
}

variable "worker_subnet_ids" {
  type        = list(string)
  description = "Subnet IDs where worker ECS service tasks are placed"
}

variable "assign_public_ip" {
  type        = bool
  default     = true
  description = "Assign public IP to Fargate tasks (true for cost-effective deployment in public subnets without NAT)"
}

variable "ecs_backend_security_group_id" {
  type        = string
  description = "Security Group ID for backend tasks"
}

variable "ecs_worker_security_group_id" {
  type        = string
  description = "Security Group ID for worker tasks"
}

variable "target_group_arn" {
  type        = string
  description = "ALB Target Group ARN for backend tasks"
}

variable "redis_host" {
  type        = string
  description = "Redis endpoint host"
}

variable "redis_port" {
  type        = number
  default     = 6379
  description = "Redis endpoint port"
}

variable "redis_use_ssl" {
  type        = bool
  default     = false
  description = "Enable SSL for Redis connections"
}

variable "cpu" {
  type        = string
  default     = "256"
  description = "Fargate CPU units (256 = 0.25 vCPU)"
}

variable "memory" {
  type        = string
  default     = "512"
  description = "Fargate Memory (512 = 512 MB)"
}

variable "log_retention_in_days" {
  type        = number
  default     = 7
  description = "CloudWatch log retention in days for cost control"
}
