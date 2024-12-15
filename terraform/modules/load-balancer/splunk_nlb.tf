resource "aws_lb" "nlb_splunk" {
  name               = var.names.nlb_name
  internal           = true
  load_balancer_type = "network"
  subnets            = [for config in var.nlb_config : config.subnet_id]

  enable_cross_zone_load_balancing = true
  tags = var.tags
}

resource "aws_lb_target_group" "nlb_target_group" {
  name     = "${var.names.nlb_name}-tg"
  port     = 8088
  protocol = "TCP"
  vpc_id   = data.aws_subnet.selected_subnets.vpc_id

  deregistration_delay = 300
  preserve_client_ip   = true

  health_check {
    enabled             = true
    port                = 8088
    protocol            = "TCP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 6
  }
}

resource "aws_lb_target_group_attachment" "nlb_fo_attachment" {
  count = length(var.nlb_config)

  target_group_arn = aws_lb_target_group.nlb_target_group.arn
  target_id        = var.nlb_config[count.index].instance_id
  port             = 8088
}

resource "aws_lb_listener" "nlb_listener" {
  load_balancer_arn = aws_lb.nlb_splunk.arn
  port              = "8088"
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.nlb_target_group.arn
  }
}