variable "project_name" {
  type        = string
  description = "Project name prefix"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where the target group resides"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs where ALB is deployed across multiple AZs"
}

variable "alb_security_group_id" {
  type        = string
  description = "Security Group ID for ALB"
}

variable "certificate_arn" {
  type        = string
  default     = ""
  description = "Optional ACM SSL/TLS certificate ARN for HTTPS listener on port 443"
}
