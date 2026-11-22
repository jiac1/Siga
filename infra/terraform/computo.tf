# ── Repositorios de imágenes ────────────────────────────────────────
resource "aws_ecr_repository" "servicio" {
  for_each             = local.servicios
  name                 = "${var.proyecto}/${each.key}"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration {
    scan_on_push = true # análisis de vulnerabilidades en cada publicación
  }
  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "servicio" {
  for_each   = aws_ecr_repository.servicio
  repository = each.value.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Conservar las 30 imágenes más recientes"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 30 }
      action       = { type = "expire" }
    }]
  })
}

# ── Clúster ECS Fargate ─────────────────────────────────────────────
resource "aws_ecs_cluster" "suite" {
  name = local.nombre
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "suite" {
  cluster_name       = aws_ecs_cluster.suite.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  default_capacity_provider_strategy {
    capacity_provider = var.ambiente == "produccion" ? "FARGATE" : "FARGATE_SPOT"
    weight            = 1
  }
}

resource "aws_cloudwatch_log_group" "servicio" {
  for_each          = local.servicios
  name              = "/ecs/${local.nombre}/${each.key}"
  retention_in_days = var.ambiente == "produccion" ? 90 : 14
}

locals {
  entorno_comun = {
    DEBUG                = "False"
    SUITE_MODE           = "suite"
    SUITE_PORTAL_URL     = "/"
    ALLOWED_HOSTS        = "*" # el ALB solo es alcanzable desde CloudFront (ver red.tf)
    CSRF_TRUSTED_ORIGINS = local.url_publica
    LOG_LEVEL            = "INFO"
    APP_VERSION          = var.version_imagen
    GUNICORN_WORKERS     = "3"
  }

  entorno_servicio = {
    core = {
      URL_PREFIX         = "core/"
      DB_NAME            = "core"
      EMAIL_BACKEND      = var.remitente_correo != "" ? "django.core.mail.backends.smtp.EmailBackend" : "django.core.mail.backends.console.EmailBackend"
      DEFAULT_FROM_EMAIL = var.remitente_correo
      EMAIL_HOST         = "email-smtp.${var.aws_region}.amazonaws.com"
    }
    "mapa-calor" = {
      URL_PREFIX = "mapa-calor/"
    }
    "estres-malla" = {
      URL_PREFIX              = "estres-malla/"
      DB_NAME                 = "estres_malla"
      AWS_STORAGE_BUCKET_NAME = aws_s3_bucket.media.bucket
      AWS_S3_REGION_NAME      = var.aws_region
    }
  }

  contenedor = {
    for nombre, svc in local.servicios : nombre => {
      name         = nombre
      image        = "${aws_ecr_repository.servicio[nombre].repository_url}:${var.version_imagen}"
      essential    = true
      portMappings = [{ containerPort = 8000, protocol = "tcp" }]
      environment = [for k, v in merge(
        local.entorno_comun,
        local.entorno_servicio[nombre],
        svc.base == null ? tomap({}) : tomap({ DB_HOST = aws_db_instance.postgres.address, DB_USER = aws_db_instance.postgres.username })
      ) : { name = k, value = v }]
      secrets = concat(
        [
          { name = "SUITE_SSO_SECRET", valueFrom = "${aws_secretsmanager_secret.app.arn}:SUITE_SSO_SECRET::" },
          { name = "SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.app.arn}:SECRET_KEY_${upper(replace(nombre, "-", "_"))}::" },
        ],
        [for clave in(svc.base == null ? [] : ["password"]) :
          { name = "DB_PASSWORD", valueFrom = "${aws_db_instance.postgres.master_user_secret[0].secret_arn}:${clave}::" }
        ]
      )
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.servicio[nombre].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = nombre
        }
      }
      readonlyRootFilesystem = false
    }
  }
}

resource "aws_ecs_task_definition" "servicio" {
  for_each                 = local.servicios
  family                   = "${local.nombre}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.servicios[each.key].cpu
  memory                   = var.servicios[each.key].memoria
  execution_role_arn       = aws_iam_role.ejecucion.arn
  task_role_arn            = aws_iam_role.tarea[each.key].arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([local.contenedor[each.key]])
}

# Tarea única de migración (la ejecuta el pipeline antes de actualizar el servicio).
resource "aws_ecs_task_definition" "migracion" {
  for_each                 = { for k, v in local.servicios : k => v if v.base != null }
  family                   = "${local.nombre}-${each.key}-migrar"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ejecucion.arn
  task_role_arn            = aws_iam_role.tarea[each.key].arn
  container_definitions    = jsonencode([merge(local.contenedor[each.key], { command = ["migrar"], portMappings = [] })])
}

resource "aws_ecs_service" "servicio" {
  for_each                          = local.servicios
  name                              = each.key
  cluster                           = aws_ecs_cluster.suite.id
  task_definition                   = aws_ecs_task_definition.servicio[each.key].arn
  desired_count                     = var.servicios[each.key].minimo
  health_check_grace_period_seconds = 60
  enable_execute_command            = true

  capacity_provider_strategy {
    capacity_provider = var.ambiente == "produccion" ? "FARGATE" : "FARGATE_SPOT"
    weight            = 1
  }

  network_configuration {
    subnets          = aws_subnet.privada[*].id
    security_groups  = [aws_security_group.servicios.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.servicio[each.key].arn
    container_name   = each.key
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true # si la nueva versión no pasa el health check, vuelve a la anterior
  }
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  lifecycle {
    # desired_count lo gestiona el autoescalado; task_definition, el pipeline de
    # despliegue (cada commit publica una revisión nueva con su imagen).
    ignore_changes = [desired_count, task_definition]
  }
  depends_on = [aws_lb_listener_rule.servicio]
}

# ── Autoescalado por CPU ────────────────────────────────────────────
resource "aws_appautoscaling_target" "servicio" {
  for_each           = local.servicios
  service_namespace  = "ecs"
  resource_id        = "service/${aws_ecs_cluster.suite.name}/${aws_ecs_service.servicio[each.key].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  min_capacity       = var.servicios[each.key].minimo
  max_capacity       = var.servicios[each.key].maximo
}

resource "aws_appautoscaling_policy" "cpu" {
  for_each           = local.servicios
  name               = "${local.nombre}-${each.key}-cpu"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = "ecs"
  resource_id        = aws_appautoscaling_target.servicio[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.servicio[each.key].scalable_dimension
  target_tracking_scaling_policy_configuration {
    target_value       = 60
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# ── Tareas programadas ──────────────────────────────────────────────
# Purga diaria de datos personales vencidos (regla RN-06, Ley 21.719).
resource "aws_ecs_task_definition" "purga" {
  family                   = "${local.nombre}-core-purga"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ejecucion.arn
  task_role_arn            = aws_iam_role.tarea["core"].arn
  container_definitions = jsonencode([merge(local.contenedor["core"], {
    command      = ["python", "manage.py", "purgar_datos_vencidos"]
    portMappings = []
  })])
}

data "aws_iam_policy_document" "asumir_scheduler" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${local.nombre}-scheduler"
  assume_role_policy = data.aws_iam_policy_document.asumir_scheduler.json
}

resource "aws_iam_role_policy" "scheduler" {
  name = "ejecutar-purga"
  role = aws_iam_role.scheduler.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["ecs:RunTask"], Resource = aws_ecs_task_definition.purga.arn_without_revision },
      {
        Effect    = "Allow"
        Action    = ["iam:PassRole"]
        Resource  = [aws_iam_role.ejecucion.arn, aws_iam_role.tarea["core"].arn]
        Condition = { StringEquals = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" } }
      }
    ]
  })
}

resource "aws_scheduler_schedule" "purga" {
  name                         = "${local.nombre}-purga-datos"
  schedule_expression          = "cron(0 4 * * ? *)" # 04:00 UTC ≈ madrugada en Chile
  schedule_expression_timezone = "UTC"
  flexible_time_window {
    mode = "OFF"
  }
  target {
    arn      = aws_ecs_cluster.suite.arn
    role_arn = aws_iam_role.scheduler.arn
    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.purga.arn_without_revision
      launch_type         = "FARGATE"
      network_configuration {
        subnets          = aws_subnet.privada[*].id
        security_groups  = [aws_security_group.servicios.id]
        assign_public_ip = false
      }
    }
  }
}
