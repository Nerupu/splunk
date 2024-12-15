locals {
  disks_configuration = [for config in module.vm-deploy.*.volumes_config : config if length(config) != 0]
  alb_configuration   = [for config in module.vm-deploy.*.alb_config : config if length(config) != 0]
  nlb_configuration   = [for config in module.vm-deploy.*.nlb_config : config if length(config) != 0]
  private_ips         = [for ip in module.vm-deploy.*.splunk_instances : ip if length(ip) != 0]

  region  = data.aws_region.current.name
  acc_num = data.aws_caller_identity.current.id
  zone-suffix = {
    eu-central-1 = "eu"
    eu-west-2    = "uk"
    us-east-1    = "na"
  }

  zreg = lookup(local.zone-suffix, local.region)

  public_zone_name = "${var.product}-${var.env}.${local.zreg}.${var.public_domain}"

  domain_name = data.terraform_remote_state.network.outputs.private_zonename
  zone_id     = data.terraform_remote_state.network.outputs.private_zoneid
  public_zone_id = data.aws_route53_zone.public.zone_id
  
  pub_domain_name = data.aws_route53_zone.public.name

}
