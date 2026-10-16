output "redis_endpoint" {
  value       = var.num_cache_clusters > 1 ? aws_elasticache_replication_group.redis.configuration_endpoint_address : aws_elasticache_replication_group.redis.primary_endpoint_address
  description = "The primary Redis connection hostname (without credentials)"
}

output "redis_port" {
  value       = aws_elasticache_replication_group.redis.port
  description = "The Redis connection port"
}

output "redis_arn" {
  value       = aws_elasticache_replication_group.redis.arn
  description = "The ARN of the ElastiCache replication group"
}
