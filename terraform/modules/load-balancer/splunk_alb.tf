resource "aws_lb" "alb_splunk" {
  name               = var.names.alb_name
  internal           = true
  load_balancer_type = "application"
  security_groups    = data.aws_security_group.aws_alb_sgs.*.id
  subnets            = [for config in var.alb_config : config.subnet_id]

  tags = var.tags
}

resource "aws_lb_target_group" "alb_target_group" {
  name       = "${var.names.alb_name}-tg"
  port       = 8000
  protocol   = "HTTP"
  vpc_id     = data.aws_subnet.selected_subnets.vpc_id
  slow_start = 0

  load_balancing_algorithm_type = "round_robin"
  deregistration_delay = 10

  stickiness {
    enabled = true
    type    = "lb_cookie"
  }

  health_check {
    enabled             = true
    port                = 8000
    interval            = 30
    protocol            = "HTTP"
    path                = "/"
    matcher             = "200-399"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 6
  }
}

resource "aws_lb_target_group_attachment" "alb_sh_attachment" {
  count = length(var.alb_config)

  target_group_arn = aws_lb_target_group.alb_target_group.arn
  target_id        = var.alb_config[count.index].instance_id
  port             = 8000
}

resource "aws_lb_listener" "alb_listener" {
  load_balancer_arn = aws_lb.alb_splunk.arn
  port              = "8000"
  protocol          = "HTTPS"
  certificate_arn   = var.cert_name
  ssl_policy         = "ELBSecurityPolicy-TLS13-1-2-2021-06"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.alb_target_group.arn
  }
}