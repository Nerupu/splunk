output "instances_list" {
  description = "The name, ID and private dns of the EC2 instances."
  value       = module.vm-deploy.*.splunk_instances
}

output "alb_dns" {
  description = "Application load balancer dns"
  value       = module.load-balancer.alb_dns
}
