module "vm-deploy" {
  source            = "./modules/vm-deploy"
  count             = length(var.instances_list)
  instance_type     = data.aws_ec2_instance_type.aws_instance_type[count.index].instance_type
  name              = var.instances_list[count.index].vm_name
  ami_name          = var.instances_list[count.index].vm_ami_name
  type_vm           = var.instances_list[count.index].vm_worker_type
  instance_profile  = data.aws_iam_instance_profile.aws_instance_profile[count.index].name
  subnet            = data.aws_subnet.aws_subnet_id[count.index].id
  security_groups   = var.instances_list[count.index].vm_sg_list
  tags              = var.instances_list[count.index].vm_tags
  root_volume_conf  = var.instances_list[count.index].root_volume
  data_volumes_conf = var.instances_list[count.index].data_volumes

}


module "mount-devices" {
  source      = "./modules/mount-devices"
  count       = length(local.disks_configuration) != 0 ? length(local.disks_configuration) : 0
  instance_id = local.disks_configuration[count.index][0].instance_id
  disks       = local.disks_configuration[count.index][0].disks
  depends_on = [
    module.vm-deploy
  ]
}

module "aws_route53_record" {
  source  = "./modules/aws_route53_record"
  count   = length(var.instances_list)
  name    = join(".", [var.instances_list[count.index].vm_name, local.domain_name])
  zone_id = local.zone_id
  type    = "A"
  ttl     = "60"
  records = local.private_ips[count.index].private_ip
  depends_on = [
    module.vm-deploy
  ]
}


module "load-balancer" {
  source     = "./modules/load-balancer"
  alb_config = local.alb_configuration
  nlb_config = local.nlb_configuration
  names      = var.load_balancer.names
  alb_sgs    = var.load_balancer.security_groups
  tags       = var.load_balancer.tags
  cert_name  =  aws_acm_certificate.searchhead.arn 
  depends_on = [
    module.vm-deploy,
    module.mount-devices,
    aws_acm_certificate.searchhead,
    aws_route53_record.searchhead_validation,
    aws_acm_certificate_validation.searchhead
  ]
}




