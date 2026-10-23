# ── Rol de ejecución (lo usa el agente de ECS: imágenes, logs y secretos) ──
data "aws_iam_policy_document" "asumir_ecs" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ejecucion" {
  name               = "${local.nombre}-ejecucion"
  assume_role_policy = data.aws_iam_policy_document.asumir_ecs.json
}

resource "aws_iam_role_policy_attachment" "ejecucion" {
  role       = aws_iam_role.ejecucion.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ejecucion_secretos" {
  name = "leer-secretos"
  role = aws_iam_role.ejecucion.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.app.arn, aws_db_instance.postgres.master_user_secret[0].secret_arn]
    }]
  })
}

# ── Roles de tarea: mínimo privilegio por servicio ──────────────────
resource "aws_iam_role" "tarea" {
  for_each           = local.servicios
  name               = "${local.nombre}-${each.key}"
  assume_role_policy = data.aws_iam_policy_document.asumir_ecs.json
}

# ECS Exec (acceso de emergencia a un contenedor, auditado en CloudTrail)
resource "aws_iam_role_policy" "tarea_exec" {
  for_each = local.servicios
  name     = "ecs-exec"
  role     = aws_iam_role.tarea[each.key].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["ssmmessages:CreateControlChannel", "ssmmessages:CreateDataChannel",
                "ssmmessages:OpenControlChannel", "ssmmessages:OpenDataChannel"]
      Resource = "*"
    }]
  })
}

# Estrés de Malla guarda los Excel subidos en S3 (solo su prefijo).
resource "aws_iam_role_policy" "estres_media" {
  name = "media-s3"
  role = aws_iam_role.tarea["estres-malla"].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.media.arn}/estres-malla/*"
      },
      {
        Effect    = "Allow"
        Action    = ["s3:ListBucket"]
        Resource  = aws_s3_bucket.media.arn
        Condition = { StringLike = { "s3:prefix" = ["estres-malla/*"] } }
      }
    ]
  })
}

# Core envía correos (comprobantes de convalidación, activación de cuentas) con SES.
resource "aws_iam_role_policy" "core_ses" {
  name = "ses-enviar"
  role = aws_iam_role.tarea["core"].id
  # Si hay remitente definido, la política solo permite enviar desde esa dirección.
  policy = var.remitente_correo == "" ? jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["ses:SendEmail", "ses:SendRawEmail"], Resource = "*" }]
    }) : jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = ["ses:SendEmail", "ses:SendRawEmail"]
      Resource  = "*"
      Condition = { StringEquals = { "ses:FromAddress" = var.remitente_correo } }
    }]
  })
}

# ── Despliegue continuo desde GitHub Actions (OIDC, sin llaves de larga duración) ──
resource "aws_iam_openid_connect_provider" "github" {
  count           = var.github_repositorio == "" ? 0 : 1
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "asumir_github" {
  count = var.github_repositorio == "" ? 0 : 1
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github[0].arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:${var.github_repositorio}:ref:refs/heads/main",
        "repo:${var.github_repositorio}:environment:${var.ambiente}",
      ]
    }
  }
}

resource "aws_iam_role" "github_despliegue" {
  count              = var.github_repositorio == "" ? 0 : 1
  name               = "${local.nombre}-github-despliegue"
  assume_role_policy = data.aws_iam_policy_document.asumir_github[0].json
}

resource "aws_iam_role_policy" "github_despliegue" {
  count = var.github_repositorio == "" ? 0 : 1
  name  = "desplegar-suite"
  role  = aws_iam_role.github_despliegue[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["ecr:GetAuthorizationToken"], Resource = "*" },
      {
        Effect   = "Allow"
        Action   = ["ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload", "ecr:PutImage", "ecr:BatchGetImage", "ecr:DescribeImages"]
        Resource = [for r in aws_ecr_repository.servicio : r.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["ecs:DescribeServices", "ecs:DescribeTaskDefinition", "ecs:RegisterTaskDefinition",
                    "ecs:UpdateService", "ecs:RunTask", "ecs:DescribeTasks", "ecs:ListTasks"]
        Resource = "*"
      },
      {
        Effect    = "Allow"
        Action    = ["iam:PassRole"]
        Resource  = concat([aws_iam_role.ejecucion.arn], [for r in aws_iam_role.tarea : r.arn])
        Condition = { StringEquals = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" } }
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket", "s3:PutObject", "s3:DeleteObject", "s3:GetObject"]
        Resource = [aws_s3_bucket.portal.arn, "${aws_s3_bucket.portal.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["cloudfront:CreateInvalidation"]
        Resource = aws_cloudfront_distribution.suite.arn
      }
    ]
  })
}
