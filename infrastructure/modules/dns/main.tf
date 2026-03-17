variable "project" {}
variable "domain_name" {}
variable "alb_dns_name" {}
variable "alb_zone_id" {}

# ─── Route53 Hosted Zone ───────────────────────────────────────────────
resource "aws_route53_zone" "main" {
  name = var.domain_name
  tags = { Project = var.project }
}

# ─── ACM Certificate ───────────────────────────────────────────────────
resource "aws_acm_certificate" "main" {
  domain_name               = var.domain_name
  subject_alternative_names = ["www.${var.domain_name}"]
  validation_method         = "DNS"
  tags                      = { Project = var.project }

  lifecycle {
    create_before_destroy = true
  }
}

# ─── DNS validation records ────────────────────────────────────────────
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  }

  zone_id = aws_route53_zone.main.zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.record]
}

# ─── Wait for certificate to be validated ─────────────────────────────
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}

# ─── A record: apex → ALB ─────────────────────────────────────────────
resource "aws_route53_record" "apex" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# ─── A record: www → ALB ──────────────────────────────────────────────
resource "aws_route53_record" "www" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# ─── Outputs ──────────────────────────────────────────────────────────
output "certificate_arn"      { value = aws_acm_certificate_validation.main.certificate_arn }
output "hosted_zone_id"       { value = aws_route53_zone.main.zone_id }
output "name_servers"         { value = aws_route53_zone.main.name_servers }
