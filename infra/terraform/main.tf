data "aws_availability_zones" "disponibles" {
  state = "available"
}

data "aws_caller_identity" "actual" {}

locals {
  nombre = "${var.proyecto}-${var.ambiente}"
  azs    = slice(data.aws_availability_zones.disponibles.names, 0, 2)

  etiquetas = {
    Proyecto   = var.proyecto
    Ambiente   = var.ambiente
    Gestionado = "terraform"
    Repositorio = "Suite-Unab"
  }

  usa_dominio = var.dominio != ""
  url_publica = local.usa_dominio ? "https://${var.dominio}" : "https://${aws_cloudfront_distribution.suite.domain_name}"

  # Catálogo de servicios con backend. El prefijo es la ruta que enruta
  # CloudFront/ALB hacia el servicio (el ALB no reescribe rutas).
  servicios = {
    core = {
      prefijo   = "core"
      base      = "core"
      prioridad = 10
    }
    "mapa-calor" = {
      prefijo   = "mapa-calor"
      base      = null
      prioridad = 20
    }
    "estres-malla" = {
      prefijo   = "estres-malla"
      base      = "estres_malla"
      prioridad = 30
    }
  }

  # Patrones de ruta para CloudFront (con y sin barra final para enrutar a Django)
  patrones_cloudfront = merge(
    { for k, v in local.servicios : "${k}_con_barra" => "/${v.prefijo}/*" },
    { for k, v in local.servicios : "${k}_sin_barra" => "/${v.prefijo}" }
  )
}
