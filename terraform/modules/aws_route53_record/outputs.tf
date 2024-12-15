output "dns_records" {
  description = "DNS host A records created"
  value = tomap({"dns_record_name" = "${aws_route53_record.private.name}"})
}
