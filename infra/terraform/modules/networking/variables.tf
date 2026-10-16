variable "project_name" {
  type        = string
  description = "Project name prefix for resource naming"
}

variable "environment" {
  type        = string
  description = "Deployment environment (e.g. dev, staging, prod)"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for the VPC"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of Availability Zones to deploy subnets into"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
  description = "CIDR blocks for public subnets (at least 2 AZs for ALB)"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
  description = "CIDR blocks for private subnets (for ElastiCache and private tasks)"
}

variable "enable_nat_gateway" {
  type        = bool
  default     = false
  description = "Set to true to provision NAT Gateway (adds ~$35/month; leave false for cost-optimized dev assessment)"
}
