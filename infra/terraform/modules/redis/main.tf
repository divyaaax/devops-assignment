# ==============================================================================
# Amazon ElastiCache for Redis Module
# Private, managed Redis instance for Celery task queuing and result storage
# ==============================================================================

# Private Subnet Group
resource "aws_elasticache_subnet_group" "redis" {
  name        = "${var.project_name}-${var.environment}-redis-subnet-group"
  subnet_ids  = var.private_subnet_ids
  description = "Private subnets for ElastiCache Redis cluster"

  tags = {
    Name        = "${var.project_name}-${var.environment}-redis-subnet-group"
    Environment = var.environment
  }
}

# ElastiCache Redis Replication Group
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project_name}-${var.environment}-redis"
  description                = "Celery task broker and result backend for ${var.project_name}"
  node_type                  = var.node_type
  num_cache_clusters         = var.num_cache_clusters
  parameter_group_name       = "default.redis7"
  port                       = 6379
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [var.redis_security_group_id]
  automatic_failover_enabled = var.num_cache_clusters > 1 ? true : false

  # Encryption & Security Settings
  at_rest_encryption_enabled = true
  transit_encryption_enabled = var.transit_encryption_enabled
  auth_token                 = var.transit_encryption_enabled && var.auth_token != null ? var.auth_token : null

  auto_minor_version_upgrade = true
  apply_immediately          = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-redis"
    Environment = var.environment
  }
}
