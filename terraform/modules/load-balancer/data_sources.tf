data "aws_subnet" "selected_subnets" {
  id = var.alb_config[0].subnet_id
}

data "aws_security_group" "aws_alb_sgs" {
  count    = length(var.alb_sgs)
  id       = var.alb_sgs[count.index]
}