resource "aws_security_group" "eaf_priv_searchhead_sg" {
  name        = "eaf-priv-searchhead-sg"
  description = "SG for Splunk SearchHead Instances"
  vpc_id      = module.ipam_vpc.vpc_id
  depends_on  = [aws_security_group.eaf_pub_searchhead_alb_sg]

  dynamic "ingress" {
    for_each = [80, 443, 8000, 8080, 8088, 8089]
    iterator = port
    content {
      description = "ALB ingress to search heads"
      from_port   = port.value
      to_port     = port.value
      protocol    = "tcp"
      security_groups = [
        aws_security_group.eaf_pub_searchhead_alb_sg.id
      ]
    }
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

  tags = merge({ "Name" = "eaf-priv-search-head-sg" },  { "private" = "true" }, { "tier" = "tier1" }, var.tags, var.sg_tags)

}
