output "url_suite" {
  description = "URL pública de la Suite"
  value       = local.url_publica
}

output "cloudfront_id" {
  description = "ID de la distribución (para invalidar caché al publicar el portal)"
  value       = aws_cloudfront_distribution.suite.id
}

output "bucket_portal" {
  description = "Bucket S3 donde se publica el front-end estático"
  value       = aws_s3_bucket.portal.bucket
}

output "ecr_repositorios" {
  description = "Repositorios de imágenes por servicio"
  value       = { for k, r in aws_ecr_repository.servicio : k => r.repository_url }
}

output "cluster_ecs" {
  value = aws_ecs_cluster.suite.name
}

output "subredes_privadas" {
  description = "Subredes para ejecutar tareas únicas (migraciones)"
  value       = aws_subnet.privada[*].id
}

output "grupo_seguridad_servicios" {
  value = aws_security_group.servicios.id
}

output "rol_github" {
  description = "ARN del rol que asume GitHub Actions (configurar como secreto AWS_ROLE_ARN)"
  value       = try(aws_iam_role.github_despliegue[0].arn, null)
}

output "rds_endpoint" {
  value     = aws_db_instance.postgres.address
  sensitive = true
}
