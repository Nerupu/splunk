data "aws_ec2_instance_type" "aws_instance_type" {
  count         = length(var.instances_list)
  instance_type = var.instances_list[count.index].vm_instance_type
}

data "aws_iam_instance_profile" "aws_instance_profile" {
  count = length(var.instances_list)
  name  = var.instances_list[count.index].vm_instance_profile
}

data "aws_subnet" "aws_subnet_id" {
  count = length(var.instances_list)
  id    = var.instances_list[count.index].vm_subnet
}

data "aws_route53_zone" "public" {
  name         = local.public_zone_name
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket         = "terraform-state-${local.acc_num}-${local.region}"
    region         = local.region
    dynamodb_table = "terraform-state-lock-${local.acc_num}-${local.region}"
    key            = "network/terraform.tfstate"
  }
}

