output "splunk_instances" {
  description = "The name, ID and dns of the EC2 instances."
  value = tomap({ "type" = "${aws_instance.splunk_vm.tags.type}",
    "instance_id" = "${aws_instance.splunk_vm.id}",
    "private_dns" = "${aws_instance.splunk_vm.private_dns}"
    "private_ip"  = "${aws_instance.splunk_vm.private_ip}"
  })
}

output "volumes_config" {
  description = "Volumes configuration data: instance id, disks."
  value       = length(var.data_volumes_conf) != 0 ? [{ "instance_id" : "${aws_instance.splunk_vm.id}", "disks" : "${var.data_volumes_conf}" }] : []
}

output "alb_config" {
  description = "Application load balancer configuration for search heads."
  value       = aws_instance.splunk_vm.tags.Type == "SearchHead" ? tomap({ "instance_id" = "${aws_instance.splunk_vm.id}", "subnet_id" = "${aws_instance.splunk_vm.subnet_id}" }) : {}
}

output "nlb_config" {
  description = "Network load balancer configuration for forwarders."
  value       = aws_instance.splunk_vm.tags.Type == "Forwarder" ? tomap({ "instance_id" = "${aws_instance.splunk_vm.id}", "subnet_id" = "${aws_instance.splunk_vm.subnet_id}" }) : {}
}