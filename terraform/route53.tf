resource "aws_route53_record" "search_alb" {
  zone_id  = local.public_zone_id
  name     = "searchhead.${local.pub_domain_name}"
  type     = "A"

  alias {
    name                   = module.load-balancer.alb_dns
    zone_id                = module.load-balancer.alb_zone_id
    evaluate_target_health = false
  }
}