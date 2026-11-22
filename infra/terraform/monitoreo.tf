# ── Alarmas y tablero operacional ───────────────────────────────────
resource "aws_sns_topic" "alertas" {
  name = "${local.nombre}-alertas"
}

resource "aws_sns_topic_subscription" "correo" {
  count     = var.correo_alertas == "" ? 0 : 1
  topic_arn = aws_sns_topic.alertas.arn
  protocol  = "email"
  endpoint  = var.correo_alertas
}

resource "aws_cloudwatch_metric_alarm" "errores_5xx" {
  for_each            = local.servicios
  alarm_name          = "${local.nombre}-${each.key}-5xx"
  alarm_description   = "Más de 10 respuestas 5xx en 5 minutos en ${each.key}"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 10
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    LoadBalancer = aws_lb.suite.arn_suffix
    TargetGroup  = aws_lb_target_group.servicio[each.key].arn_suffix
  }
  alarm_actions = [aws_sns_topic.alertas.arn]
  ok_actions    = [aws_sns_topic.alertas.arn]
}

resource "aws_cloudwatch_metric_alarm" "latencia" {
  for_each            = local.servicios
  alarm_name          = "${local.nombre}-${each.key}-latencia-p95"
  alarm_description   = "Latencia p95 sobre 2 s durante 10 minutos en ${each.key}"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  extended_statistic  = "p95"
  period              = 300
  evaluation_periods  = 2
  threshold           = 2
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    LoadBalancer = aws_lb.suite.arn_suffix
    TargetGroup  = aws_lb_target_group.servicio[each.key].arn_suffix
  }
  alarm_actions = [aws_sns_topic.alertas.arn]
}

resource "aws_cloudwatch_metric_alarm" "destinos_no_sanos" {
  for_each            = local.servicios
  alarm_name          = "${local.nombre}-${each.key}-sin-instancias-sanas"
  alarm_description   = "El servicio ${each.key} no tiene tareas sanas"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HealthyHostCount"
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  dimensions = {
    LoadBalancer = aws_lb.suite.arn_suffix
    TargetGroup  = aws_lb_target_group.servicio[each.key].arn_suffix
  }
  alarm_actions = [aws_sns_topic.alertas.arn]
  ok_actions    = [aws_sns_topic.alertas.arn]
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${local.nombre}-rds-cpu"
  alarm_description   = "CPU de RDS sobre 80% durante 15 minutos"
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  dimensions          = { DBInstanceIdentifier = aws_db_instance.postgres.identifier }
  alarm_actions       = [aws_sns_topic.alertas.arn]
}

resource "aws_cloudwatch_metric_alarm" "rds_almacenamiento" {
  alarm_name          = "${local.nombre}-rds-almacenamiento"
  alarm_description   = "Menos de 2 GB libres en RDS"
  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  statistic           = "Minimum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 2147483648
  comparison_operator = "LessThanThreshold"
  dimensions          = { DBInstanceIdentifier = aws_db_instance.postgres.identifier }
  alarm_actions       = [aws_sns_topic.alertas.arn]
}

resource "aws_cloudwatch_dashboard" "suite" {
  dashboard_name = local.nombre
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric", x = 0, y = 0, width = 12, height = 6
        properties = {
          title  = "Peticiones por servicio"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [for k, _ in local.servicios :
            ["AWS/ApplicationELB", "RequestCount", "TargetGroup", aws_lb_target_group.servicio[k].arn_suffix,
             "LoadBalancer", aws_lb.suite.arn_suffix, { label = k }]]
        }
      },
      {
        type = "metric", x = 12, y = 0, width = 12, height = 6
        properties = {
          title  = "Latencia p95 (s)"
          region = var.aws_region
          stat   = "p95"
          period = 300
          metrics = [for k, _ in local.servicios :
            ["AWS/ApplicationELB", "TargetResponseTime", "TargetGroup", aws_lb_target_group.servicio[k].arn_suffix,
             "LoadBalancer", aws_lb.suite.arn_suffix, { label = k }]]
        }
      },
      {
        type = "metric", x = 0, y = 6, width = 12, height = 6
        properties = {
          title  = "CPU de los servicios (%)"
          region = var.aws_region
          stat   = "Average"
          period = 300
          metrics = [for k, _ in local.servicios :
            ["AWS/ECS", "CPUUtilization", "ClusterName", aws_ecs_cluster.suite.name, "ServiceName", k, { label = k }]]
        }
      },
      {
        type = "metric", x = 12, y = 6, width = 12, height = 6
        properties = {
          title   = "RDS"
          region  = var.aws_region
          period  = 300
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.postgres.identifier],
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", aws_db_instance.postgres.identifier, { yAxis = "right" }]
          ]
        }
      }
    ]
  })
}
