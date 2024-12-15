resource "aws_acm_certificate" "searchhead" {
  domain_name       = "searchhead.${local.pub_domain_name}"
  validation_method = "DNS"

    lifecycle {
    create_before_destroy = true
  }

  tags = var.tags
}

resource "aws_route53_record" "searchhead_validation" {
  for_each = {
    for dvo in aws_acm_certificate.searchhead.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = local.public_zone_id
}

resource "aws_acm_certificate_validation" "searchhead" {
  certificate_arn         = aws_acm_certificate.searchhead.arn
  validation_record_fqdns = [for record in aws_route53_record.searchhead_validation : record.fqdn]
}