output "alb_dns" {
  description = "Application load balancer search heads dns."
  value       = aws_lb.alb_splunk.dns_name
}

output "alb_zone_id" {
  description = "Application load balancer search heads zoneID."
  value       = aws_lb.alb_splunk.zone_id
}