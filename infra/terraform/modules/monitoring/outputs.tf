output "backend_cpu_alarm_arn" {
  value       = aws_cloudwatch_metric_alarm.backend_cpu_high.arn
  description = "ARN of the Backend CPU High alarm"
}

output "alb_unhealthy_hosts_alarm_arn" {
  value       = aws_cloudwatch_metric_alarm.alb_unhealthy_hosts.arn
  description = "ARN of the ALB Unhealthy Hosts alarm"
}
