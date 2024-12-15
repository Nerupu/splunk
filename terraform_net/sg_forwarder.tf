resource "aws_security_group" "eaf_pub_forwarder_sg" {
  name        = "eaf-pub-forwarder-sg"
  description = "SG for Splunk Forwarders"
  vpc_id      = module.ipam_vpc.vpc_id
  ingress {
    description = "Allow traffic from probes to forwarders"
    from_port   = 9981
    to_port     = 9999
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Splunk web/API access"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HEC connectivity"
    from_port   = 8088
    to_port     = 8088
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Splunk to Splunk between all nodes, including forwarders "
    from_port   = 8089
    to_port     = 8089
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

  tags = merge({ "Name" = "eaf-pub-forwarder-sg" }, { "private" = "true" }, { "tier" = "tier2" }, var.tags, var.sg_tags)
}
