variable "project_name" {
  type        = string
  description = "Project name prefix"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "ecs_cluster_name" {
  type        = string
  description = "ECS Cluster Name to monitor"
}

variable "backend_service_name" {
  type        = string
  description = "Backend ECS Service Name"
}

variable "worker_service_name" {
  type        = string
  description = "Worker ECS Service Name"
}

variable "alb_arn_suffix" {
  type        = string
  description = "ALB ARN Suffix for CloudWatch metrics"
}

variable "target_group_arn_suffix" {
  type        = string
  description = "Target Group ARN Suffix for CloudWatch metrics"
}
