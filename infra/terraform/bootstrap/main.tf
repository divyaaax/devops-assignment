# ==============================================================================
# Terraform State Bootstrap
# Provisions S3 Bucket and DynamoDB Table for Secure Remote State & Locking
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for terraform remote state backend"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment name"
}

variable "project_name" {
  type        = string
  default     = "devops-assessment"
  description = "Project identifier"
}

# S3 Bucket for Remote State
resource "aws_s3_bucket" "terraform_state" {
  bucket        = "${var.project_name}-tfstate-${var.environment}"
  force_destroy = false

  tags = {
    Name        = "${var.project_name}-tfstate-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Enable S3 Bucket Versioning for state history & disaster recovery
resource "aws_s3_bucket_versioning" "state_versioning" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable AES256 Server-Side Encryption by default
resource "aws_s3_bucket_server_side_encryption_configuration" "state_encryption" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all public access to S3 state bucket
resource "aws_s3_bucket_public_access_block" "state_public_access_block" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB Table for Distributed State Locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "${var.project_name}-tflocks-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-tflocks-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.terraform_state.id
  description = "The S3 bucket name to use in backend.tf"
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.terraform_locks.name
  description = "The DynamoDB table name for state locking in backend.tf"
}
