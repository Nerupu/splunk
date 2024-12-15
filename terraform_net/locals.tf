locals {
  azs                 = formatlist("${data.aws_region.current.name}%s", distinct([for az in var.azs_list : az]))
  splunk_net          = tolist([for cidr in data.aws_vpc_ipam_pool_cidrs.cnet.ipam_pool_cidrs : cidr.cidr if cidr.state == "provisioned"])[0]
  netmask             = split("/", local.splunk_net)[1]
  privt_netmask       = var.privt_netmask
  other_netmask       = var.other_netmask
  private_num         = var.private_num
  public_num          = var.public_num
  intra_num           = var.intra_num
  total_sub_num       = local.private_num + local.public_num + local.intra_num
  new_bits            = tolist(concat([for k in range(local.private_num) : local.privt_netmask], [for k in range(local.public_num) : local.other_netmask], [for k in range(local.intra_num) : local.other_netmask]))
  private_subnets     = [for k in range(local.total_sub_num) : cidrsubnets(local.splunk_net, local.new_bits...)[k] if k <= (local.private_num - 1)]
  public_subnets      = [for k in range(local.total_sub_num) : cidrsubnets(local.splunk_net, local.new_bits...)[k] if k == ((local.private_num + local.public_num) - 1)]
  intra_subnets       = [for k in range(local.total_sub_num) : cidrsubnets(local.splunk_net, local.new_bits...)[k] if k >= (local.total_sub_num - local.intra_num)]
  public_subnet_tags  = var.public_subnet_tags
  intra_subnet_tags   = var.intra_subnet_tags
  private_subnet_tags = var.private_subnet_tags
  tags                = var.tags

  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  region-suffix = {
    eu-central-1 = "eu"
    eu-west-2    = "uk"
    us-east-1    = "us"
  }
  suffix = lookup(local.region-suffix, local.region)
  zone-suffix = {
    eu-central-1 = "eu"
    eu-west-2    = "uk"
    us-east-1    = "na"
  }

  zreg                = lookup(local.zone-suffix, local.region)
  hosted_zone = "${var.product}-${var.env}.${local.zreg}.${var.domain}"
}