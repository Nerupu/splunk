module "ipam_vpc" {
  source            = "terraform-aws-modules/vpc/aws"
  version           = "5.1.1"
  name              = "eaf-splunk-${data.aws_region.current.name}"
  ipv4_ipam_pool_id = data.aws_vpc_ipam_pool.ipam.id
  azs               = local.azs
  cidr              = local.splunk_net
  private_subnets   = local.private_subnets
  public_subnets    = local.public_subnets
  intra_subnets     = local.intra_subnets

  create_database_subnet_group  = false
  manage_default_network_acl    = false
  manage_default_route_table    = false
  manage_default_security_group = false

  enable_dns_hostnames = true
  enable_dns_support   = true

  enable_nat_gateway     = false
  create_igw             = false
  create_egress_only_igw = false

  private_subnet_tags = merge(local.private_subnet_tags, local.tags)
  public_subnet_tags  = merge(local.public_subnet_tags, local.tags)
  intra_subnet_tags   = merge(local.intra_subnet_tags, local.tags)
  tags                = local.tags


}

resource "aws_route53_zone" "private" {
  name = data.aws_route53_zone.domain.name
  vpc {
    vpc_id = module.ipam_vpc.vpc_id
  }

  tags = var.tags
}