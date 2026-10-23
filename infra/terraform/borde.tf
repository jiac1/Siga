# ── Balanceador de aplicaciones (ALB) ───────────────────────────────
# Solo recibe tráfico de CloudFront. Enruta por prefijo de ruta a cada
# servicio ECS; las rutas no se reescriben (los servicios conocen su prefijo).

resource "aws_lb" "suite" {
  name                       = local.nombre
  load_balancer_type         = "application"
  internal                   = false
  security_groups            = [aws_security_group.alb.id]
  subnets                    = aws_subnet.publica[*].id
  drop_invalid_header_fields = true
  idle_timeout               = 120
}

resource "aws_lb_target_group" "servicio" {
  for_each             = local.servicios
  name                 = substr("${local.nombre}-${each.key}", 0, 32)
  port                 = 8000
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = aws_vpc.principal.id
  deregistration_delay = 30
  health_check {
    path                = "/${each.value.prefijo}/salud/"
    matcher             = "200"
    interval            = 20
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

# Certificado regional para el ALB (CloudFront → ALB por HTTPS).
resource "aws_acm_certificate" "alb" {
  count             = local.usa_dominio ? 1 : 0
  domain_name       = "origen.${var.dominio}"
  validation_method = "DNS"
  lifecycle { create_before_destroy = true }
}

resource "aws_route53_record" "validacion_alb" {
  for_each = local.usa_dominio ? {
    for o in aws_acm_certificate.alb[0].domain_validation_options : o.domain_name => o
  } : {}
  zone_id = var.zona_route53_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  records = [each.value.resource_record_value]
  ttl     = 300
}

resource "aws_acm_certificate_validation" "alb" {
  count                   = local.usa_dominio ? 1 : 0
  certificate_arn         = aws_acm_certificate.alb[0].arn
  validation_record_fqdns = [for r in aws_route53_record.validacion_alb : r.fqdn]
}

resource "aws_route53_record" "origen" {
  count   = local.usa_dominio ? 1 : 0
  zone_id = var.zona_route53_id
  name    = "origen.${var.dominio}"
  type    = "A"
  alias {
    name                   = aws_lb.suite.dns_name
    zone_id                = aws_lb.suite.zone_id
    evaluate_target_health = true
  }
}

# Encabezado secreto que CloudFront agrega: el ALB rechaza cualquier petición sin él.
resource "random_password" "encabezado_origen" {
  length  = 48
  special = false
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.suite.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type = local.usa_dominio ? "redirect" : "fixed-response"
    dynamic "redirect" {
      for_each = local.usa_dominio ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
    dynamic "fixed_response" {
      for_each = local.usa_dominio ? [] : [1]
      content {
        content_type = "text/plain"
        message_body = "No encontrado"
        status_code  = "404"
      }
    }
  }
}

# Con dominio propio todo el tramo CloudFront → ALB va por HTTPS. Sin dominio,
# CloudFront habla HTTP con el ALB (tráfico dentro de la red de AWS).
resource "aws_lb_listener" "https" {
  count             = local.usa_dominio ? 1 : 0
  load_balancer_arn = aws_lb.suite.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.alb[0].certificate_arn
  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "No encontrado"
      status_code  = "404"
    }
  }
}

resource "aws_lb_listener_rule" "servicio" {
  for_each     = local.servicios
  listener_arn = local.usa_dominio ? aws_lb_listener.https[0].arn : aws_lb_listener.http.arn
  priority     = each.value.prioridad
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.servicio[each.key].arn
  }
  condition {
    path_pattern {
      values = ["/${each.value.prefijo}/*"]
    }
  }
  condition {
    http_header {
      http_header_name = "X-Origen-Suite"
      values           = [random_password.encabezado_origen.result]
    }
  }
}

# ── CloudFront: dominio único para el portal y los servicios ────────
resource "aws_acm_certificate" "cdn" {
  count             = local.usa_dominio ? 1 : 0
  provider          = aws.us_east_1
  domain_name       = var.dominio
  validation_method = "DNS"
  lifecycle { create_before_destroy = true }
}

resource "aws_route53_record" "validacion_cdn" {
  for_each = local.usa_dominio ? {
    for o in aws_acm_certificate.cdn[0].domain_validation_options : o.domain_name => o
  } : {}
  zone_id = var.zona_route53_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  records = [each.value.resource_record_value]
  ttl     = 300
}

resource "aws_acm_certificate_validation" "cdn" {
  count                   = local.usa_dominio ? 1 : 0
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.cdn[0].arn
  validation_record_fqdns = [for r in aws_route53_record.validacion_cdn : r.fqdn]
}

resource "aws_cloudfront_origin_access_control" "portal" {
  name                              = "${local.nombre}-portal"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_cloudfront_cache_policy" "optimizada" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_cache_policy" "sin_cache" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "todo_menos_host" {
  name = "Managed-AllViewerExceptHostHeader"
}

data "aws_cloudfront_response_headers_policy" "seguridad" {
  name = "Managed-SecurityHeadersPolicy"
}

resource "aws_cloudfront_distribution" "suite" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Suite UNAB (${var.ambiente})"
  default_root_object = "index.html"
  price_class         = "PriceClass_All" # incluye nodos en Sudamérica (Santiago)
  aliases             = local.usa_dominio ? [var.dominio] : []
  web_acl_id          = var.habilitar_waf ? aws_wafv2_web_acl.suite[0].arn : null

  origin {
    origin_id                = "portal"
    domain_name              = aws_s3_bucket.portal.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.portal.id
  }

  origin {
    origin_id   = "servicios"
    domain_name = local.usa_dominio ? "origen.${var.dominio}" : aws_lb.suite.dns_name
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = local.usa_dominio ? "https-only" : "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
      origin_read_timeout    = 60
    }
    custom_header {
      name  = "X-Origen-Suite"
      value = random_password.encabezado_origen.result
    }
  }

  default_cache_behavior {
    target_origin_id           = "portal"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD", "OPTIONS"]
    cached_methods             = ["GET", "HEAD"]
    compress                   = true
    cache_policy_id            = data.aws_cloudfront_cache_policy.optimizada.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.seguridad.id
  }

  dynamic "ordered_cache_behavior" {
    for_each = local.servicios
    content {
      path_pattern               = "/${ordered_cache_behavior.value.prefijo}/*"
      target_origin_id           = "servicios"
      viewer_protocol_policy     = "redirect-to-https"
      allowed_methods            = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
      cached_methods             = ["GET", "HEAD"]
      compress                   = true
      cache_policy_id            = data.aws_cloudfront_cache_policy.sin_cache.id
      origin_request_policy_id   = data.aws_cloudfront_origin_request_policy.todo_menos_host.id
      response_headers_policy_id = data.aws_cloudfront_response_headers_policy.seguridad.id
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = !local.usa_dominio
    acm_certificate_arn            = local.usa_dominio ? aws_acm_certificate_validation.cdn[0].certificate_arn : null
    ssl_support_method             = local.usa_dominio ? "sni-only" : null
    minimum_protocol_version       = local.usa_dominio ? "TLSv1.2_2021" : null
  }
}

resource "aws_route53_record" "suite" {
  for_each = local.usa_dominio ? toset(["A", "AAAA"]) : toset([])
  zone_id  = var.zona_route53_id
  name     = var.dominio
  type     = each.key
  alias {
    name                   = aws_cloudfront_distribution.suite.domain_name
    zone_id                = aws_cloudfront_distribution.suite.hosted_zone_id
    evaluate_target_health = false
  }
}

# ── WAF opcional (reglas administradas de AWS) ──────────────────────
resource "aws_wafv2_web_acl" "suite" {
  count    = var.habilitar_waf ? 1 : 0
  provider = aws.us_east_1
  name     = local.nombre
  scope    = "CLOUDFRONT"
  default_action {
    allow {}
  }
  rule {
    name     = "reglas-comunes"
    priority = 1
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
        rule_action_override {
          name = "SizeRestrictions_BODY" # permite subir Excel/PDF de hasta 25 MB
          action_to_use {
            count {}
          }
        }
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "reglas-comunes"
      sampled_requests_enabled   = true
    }
  }
  rule {
    name     = "limite-por-ip"
    priority = 2
    action {
      block {}
    }
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "limite-por-ip"
      sampled_requests_enabled   = true
    }
  }
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = local.nombre
    sampled_requests_enabled   = true
  }
}
