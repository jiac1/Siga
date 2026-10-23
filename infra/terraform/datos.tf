# ── Amazon RDS for PostgreSQL ───────────────────────────────────────
resource "aws_db_subnet_group" "datos" {
  name       = local.nombre
  subnet_ids = aws_subnet.datos[*].id
}

resource "aws_db_parameter_group" "pg16" {
  name   = "${local.nombre}-pg16"
  family = "postgres16"
  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }
  parameter {
    name  = "log_min_duration_statement"
    value = "1000" # registra consultas de más de 1 s
  }
}

resource "aws_db_instance" "postgres" {
  identifier                   = local.nombre
  engine                       = "postgres"
  engine_version               = "16"
  instance_class               = var.rds_clase
  allocated_storage            = var.rds_almacenamiento_gb
  max_allocated_storage        = var.rds_almacenamiento_gb * 5
  storage_type                 = "gp3"
  storage_encrypted            = true
  db_name                      = "core"
  username                     = "suite_admin"
  manage_master_user_password  = true # contraseña rotada y guardada por RDS en Secrets Manager
  multi_az                     = var.rds_multi_az
  db_subnet_group_name         = aws_db_subnet_group.datos.name
  vpc_security_group_ids       = [aws_security_group.rds.id]
  parameter_group_name         = aws_db_parameter_group.pg16.name
  publicly_accessible          = false
  backup_retention_period      = var.ambiente == "produccion" ? 14 : 3
  backup_window                = "06:00-07:00" # 02:00-03:00 hora de Chile
  maintenance_window           = "sun:07:00-sun:08:00"
  deletion_protection          = var.ambiente == "produccion"
  skip_final_snapshot          = var.ambiente != "produccion"
  final_snapshot_identifier    = var.ambiente == "produccion" ? "${local.nombre}-final" : null
  performance_insights_enabled = true
  auto_minor_version_upgrade   = true
  copy_tags_to_snapshot        = true
}

# ── Buckets S3 ──────────────────────────────────────────────────────
resource "aws_s3_bucket" "portal" {
  bucket = "${local.nombre}-portal-${data.aws_caller_identity.actual.account_id}"
}

resource "aws_s3_bucket" "media" {
  bucket = "${local.nombre}-media-${data.aws_caller_identity.actual.account_id}"
}

resource "aws_s3_bucket_public_access_block" "bloqueo" {
  for_each                = { portal = aws_s3_bucket.portal.id, media = aws_s3_bucket.media.id }
  bucket                  = each.value
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cifrado" {
  for_each = { portal = aws_s3_bucket.portal.id, media = aws_s3_bucket.media.id }
  bucket   = each.value
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "portal" {
  bucket = aws_s3_bucket.portal.id
  versioning_configuration {
    status = "Enabled" # permite volver a una versión anterior del front-end
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "media" {
  bucket = aws_s3_bucket.media.id
  rule {
    id     = "archivos-subidos"
    status = "Enabled"
    filter {}
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
    expiration {
      days = 730 # política de retención de archivos de análisis (2 años)
    }
  }
}

resource "aws_s3_bucket_policy" "portal" {
  bucket = aws_s3_bucket.portal.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "SoloCloudFront"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.portal.arn}/*"
      Condition = { StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.suite.arn } }
    }]
  })
}

# ── Secretos de aplicación ──────────────────────────────────────────
resource "random_password" "sso" {
  length  = 64
  special = false
}

resource "random_password" "django" {
  for_each = local.servicios
  length   = 64
  special  = false
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "${local.nombre}/aplicacion"
  description             = "Secretos de Suite UNAB (SSO y SECRET_KEY de cada servicio)"
  recovery_window_in_days = var.ambiente == "produccion" ? 30 : 0
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode(merge(
    { SUITE_SSO_SECRET = random_password.sso.result },
    { for nombre, _ in local.servicios : "SECRET_KEY_${upper(replace(nombre, "-", "_"))}" => random_password.django[nombre].result }
  ))
}
