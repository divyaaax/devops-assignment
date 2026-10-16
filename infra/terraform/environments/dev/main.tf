# ==============================================================================
# Development Environment Infrastructure Composition
# Wires together Networking, ECR, Load Balancer, ElastiCache Redis, ECS & Monitoring
# ==============================================================================

# 1. Custom VPC & Networking
module "networking" {
  source = "../../modules/networking"

  project_name        = var.project_name
  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  enable_nat_gateway  = var.enable_nat_gateway
}

# 2. Elastic Container Registry (ECR)
module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name
  environment  = var.environment
}

# 3. Application Load Balancer (ALB)
module "load_balancer" {
  source = "../../modules/load_balancer"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  alb_security_group_id = module.networking.alb_security_group_id
}

# 4. Amazon ElastiCache for Redis
module "redis" {
  source = "../../modules/redis"

  project_name            = var.project_name
  environment             = var.environment
  private_subnet_ids      = module.networking.private_subnet_ids
  redis_security_group_id = module.networking.redis_security_group_id
  node_type               = "cache.t4g.micro"
  num_cache_clusters      = 1
}

# 5. Amazon ECS Fargate Cluster & Services
module "ecs" {
  source = "../../modules/ecs"

  project_name                  = var.project_name
  environment                   = var.environment
  aws_region                    = var.aws_region
  backend_image                 = var.backend_image != "public.ecr.aws/docker/library/python:3.11-slim" ? var.backend_image : module.ecr.backend_repository_url
  worker_image                  = var.worker_image != "public.ecr.aws/docker/library/python:3.11-slim" ? var.worker_image : module.ecr.worker_repository_url
  backend_subnet_ids            = var.enable_nat_gateway ? module.networking.private_subnet_ids : module.networking.public_subnet_ids
  worker_subnet_ids             = var.enable_nat_gateway ? module.networking.private_subnet_ids : module.networking.public_subnet_ids
  assign_public_ip              = var.enable_nat_gateway ? false : true
  ecs_backend_security_group_id = module.networking.ecs_backend_security_group_id
  ecs_worker_security_group_id  = module.networking.ecs_worker_security_group_id
  target_group_arn              = module.load_balancer.target_group_arn
  redis_host                    = module.redis.redis_endpoint
  redis_port                    = module.redis.redis_port
  redis_use_ssl                 = false
  cpu                           = var.fargate_cpu
  memory                        = var.fargate_memory
  log_retention_in_days         = var.log_retention_days
}

# 6. CloudWatch Alarms & Observability
module "monitoring" {
  source = "../../modules/monitoring"

  project_name            = var.project_name
  environment             = var.environment
  ecs_cluster_name        = module.ecs.cluster_name
  backend_service_name    = module.ecs.backend_service_name
  worker_service_name     = module.ecs.worker_service_name
  alb_arn_suffix          = module.load_balancer.alb_arn_suffix
  target_group_arn_suffix = module.load_balancer.target_group_arn_suffix
}
