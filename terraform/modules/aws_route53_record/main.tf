resource "aws_route53_record" "private" {
    name                     = var.name
    zone_id                  = var.zone_id
    type                     = "A"
    ttl                      = "60"
    records                  = [var.records]
  }