output "alb_arn" {
  value       = aws_lb.main.arn
  description = "ARN of the Application Load Balancer"
}

output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "Public DNS name of the ALB to access the application"
}

output "alb_zone_id" {
  value       = aws_lb.main.zone_id
  description = "Canonical hosted zone ID of the ALB (for Route53 alias records)"
}

output "target_group_arn" {
  value       = aws_lb_target_group.backend.arn
  description = "ARN of the backend Target Group"
}

output "alb_arn_suffix" {
  value       = aws_lb.main.arn_suffix
  description = "ARN Suffix of ALB for CloudWatch metrics"
}

output "target_group_arn_suffix" {
  value       = aws_lb_target_group.backend.arn_suffix
  description = "ARN Suffix of Target Group for CloudWatch metrics"
}
