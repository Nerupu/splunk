resource "aws_security_group" "eaf_priv_splunk_host_sg" {
  name        = "eaf_priv_splunk_host_sg"
  description = "SG for Splunk Search Head Instances"
  vpc_id      = module.ipam_vpc.vpc_id
  ingress {
    description = "Splunk web/API access"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "All Splunk communications"
    from_port   = 8000
    to_port     = 8999
    protocol    = "tcp"
    cidr_blocks = ["${module.ipam_vpc.vpc_cidr_block}"]
  }

  dynamic "ingress" {
    for_each = [80, 443, 22]
    iterator = port
    content {
      description = "All management connectivity in VPC"
      from_port   = port.value
      to_port     = port.value
      protocol    = "tcp"
      cidr_blocks = ["${module.ipam_vpc.vpc_cidr_block}"]
    }
  }
  egress {
    description = "Allow all IP and Ports outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge({ "Name" = "eaf-priv-splunk-host-sg" }, { "private" = "true" }, { "tier" = "tier1" }, var.tags, var.sg_tags)
}
