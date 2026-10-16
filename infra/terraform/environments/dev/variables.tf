# ==============================================================================
# Environment Variables Definition
# ==============================================================================

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Target AWS Region"
}

variable "project_name" {
  type        = string
  default     = "devops-assessment"
  description = "Project name prefix used for all provisioned cloud resources"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Deployment environment name (dev, staging, prod)"
}

variable "availability_zones" {
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
  description = "List of Availability Zones for high-availability multi-AZ deployment"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "Primary CIDR block for the custom VPC"
}

variable "enable_nat_gateway" {
  type        = bool
  default     = false
  description = "Whether to provision an AWS NAT Gateway. Set to false for cost-optimized assessment ($35/mo savings)"
}

variable "backend_image" {
  type        = string
  default     = "public.ecr.aws/docker/library/python:3.11-slim"
  description = "Initial Docker image URI for backend (updated by CI/CD deployment pipeline with ECR SHA)"
}

variable "worker_image" {
  type        = string
  default     = "public.ecr.aws/docker/library/python:3.11-slim"
  description = "Initial Docker image URI for worker (updated by CI/CD deployment pipeline with ECR SHA)"
}

variable "fargate_cpu" {
  type        = string
  default     = "256"
  description = "Fargate Task CPU allocation (256 = 0.25 vCPU)"
}

variable "fargate_memory" {
  type        = string
  default     = "512"
  description = "Fargate Task Memory allocation in MB"
}

variable "log_retention_days" {
  type        = number
  default     = 7
  description = "CloudWatch logs retention period in days"
}
