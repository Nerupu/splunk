resource "aws_security_group" "eaf_priv_indexer_sg" {
  name        = "eaf_priv_indexer_sg"
  description = "SG for Splunk Search Head Instances"
  vpc_id      = module.ipam_vpc.vpc_id
  ingress {
    description = "Splunk intermediate tier access"
    from_port   = 9997
    to_port     = 9997
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow all ingress within VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["${module.ipam_vpc.vpc_cidr_block}"]
  }

  egress {
    description = "Allow all IP and Ports outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge({ "Name" = "eaf-priv-indexer-sg" }, { "private" = "true" }, { "tier" = "tier1" }, var.tags, var.sg_tags)
}
