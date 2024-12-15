output "az" {
  value = module.ipam_vpc.azs
}

output "private_tier1_subnets" {
  value = module.ipam_vpc.private_subnets
}

output "public_subnets" {
  value = module.ipam_vpc.public_subnets
}

output "private_tier2_subnets" {
  value = module.ipam_vpc.intra_subnets
}

output "vpc_id" {
  value = module.ipam_vpc.vpc_id
}

output "sg_forwarder" {
  value = aws_security_group.eaf_pub_forwarder_sg.id
}

output "sg_serch_head_alb" {
  value = aws_security_group.eaf_pub_searchhead_alb_sg.id
}

output "sg_serch_head" {
  value = aws_security_group.eaf_priv_searchhead_sg.id
}

output "sg_indexer" {
  value = aws_security_group.eaf_priv_indexer_sg.id
}

output "sg_splunk_host" {
  value = aws_security_group.eaf_priv_splunk_host_sg.id
}

output "SSMInstanceProfile" {
  value = aws_iam_instance_profile.this.name
}

output "SSMInstanceRole" {
  value = aws_iam_role.this.name
} 

output "private_zonename" {
  value = aws_route53_zone.private.name
}

output "private_zoneid" {
  value = aws_route53_zone.private.id
}