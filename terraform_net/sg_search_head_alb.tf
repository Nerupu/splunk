resource "aws_security_group" "eaf_pub_searchhead_alb_sg" {
  name        = "eaf-pub-searchhead-alb-sg"
  description = "SG for Splunk SearchHead ALB"
  vpc_id      = module.ipam_vpc.vpc_id
  dynamic "ingress" {
    for_each = [80, 443, 8000, 8080, 8088]
    iterator = port
    content {
      from_port   = port.value
      to_port     = port.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    description = "Allow all IP and Ports outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge({ "Name" = "eaf-pub-search-head-lb-sg" }, { "private" = "true" }, { "tier" = "tier1" }, var.tags, var.sg_tags)
}
