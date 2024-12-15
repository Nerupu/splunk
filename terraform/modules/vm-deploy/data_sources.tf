data "aws_ami" "ami_id" {
  owners      = concat(["self", "amazon"], [local.ccp_ami_owner])
  most_recent = true
  filter {
    name   = "name"
    values = ["${var.ami_name}*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["${local.ami_virtualization_type}"]
  }
  filter {
    name   = "root-device-type"
    values = ["${local.ami_root_device_type}"]
  }
  filter {
    name   = "architecture"
    values = ["${local.ami_architecture}"]
  }
}

data "aws_security_group" "aws_sgs" {
  count = length(var.security_groups)
  id    = var.security_groups[count.index]
}