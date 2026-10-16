variable "project_name" {
  type        = string
  description = "Project name prefix"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs where Redis cluster nodes are isolated"
}

variable "redis_security_group_id" {
  type        = string
  description = "Security Group ID restricting access to Redis port 6379"
}

variable "node_type" {
  type        = string
  default     = "cache.t4g.micro"
  description = "ElastiCache node instance type (t4g.micro is cost-optimized Graviton2)"
}

variable "num_cache_clusters" {
  type        = number
  default     = 1
  description = "Number of cache clusters (1 for standalone dev assessment, 2+ with multi-AZ for prod)"
}

variable "transit_encryption_enabled" {
  type        = bool
  default     = false
  description = "Enable TLS in-transit encryption (requires rediss:// connection protocol)"
}

variable "auth_token" {
  type        = string
  default     = null
  sensitive   = true
  description = "Optional Redis AUTH password (requires transit_encryption_enabled = true)"
}
