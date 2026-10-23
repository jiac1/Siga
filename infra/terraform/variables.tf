variable "proyecto" {
  description = "Prefijo de nombres de recursos"
  type        = string
  default     = "suite-unab"
}

variable "ambiente" {
  description = "staging | produccion"
  type        = string
  validation {
    condition     = contains(["staging", "produccion"], var.ambiente)
    error_message = "ambiente debe ser staging o produccion."
  }
}

variable "aws_region" {
  description = "Región principal. sa-east-1 (São Paulo) minimiza la latencia desde Chile."
  type        = string
  default     = "sa-east-1"
}

variable "dominio" {
  description = "Dominio público de la Suite (ej. suite.unab.cl). Vacío = usar el dominio por defecto de CloudFront."
  type        = string
  default     = ""
}

variable "zona_route53_id" {
  description = "ID de la zona alojada en Route 53 del dominio (solo si dominio != \"\")."
  type        = string
  default     = ""
}

variable "version_imagen" {
  description = "Etiqueta de imagen ECR a desplegar (la publica el pipeline: sha del commit)."
  type        = string
  default     = "latest"
}

variable "cidr_vpc" {
  type    = string
  default = "10.40.0.0/16"
}

variable "rds_clase" {
  description = "Clase de instancia RDS PostgreSQL"
  type        = string
  default     = "db.t4g.micro"
}

variable "rds_multi_az" {
  description = "Alta disponibilidad de la base de datos (recomendado en producción)"
  type        = bool
  default     = false
}

variable "rds_almacenamiento_gb" {
  type    = number
  default = 20
}

variable "nat_unico" {
  description = "Un solo NAT Gateway (más barato; en producción crítica usar uno por AZ)"
  type        = bool
  default     = true
}

variable "habilitar_waf" {
  description = "Asocia AWS WAF (reglas administradas) a CloudFront"
  type        = bool
  default     = false
}

variable "correo_alertas" {
  description = "Correo que recibe las alarmas de CloudWatch (vacío = sin suscripción)"
  type        = string
  default     = ""
}

variable "github_repositorio" {
  description = "owner/repo de GitHub autorizado a desplegar vía OIDC (vacío = no crear el rol)"
  type        = string
  default     = ""
}

variable "remitente_correo" {
  description = "Remitente de correos transaccionales (requiere identidad verificada en SES)"
  type        = string
  default     = ""
}

variable "servicios" {
  description = "Dimensionamiento por servicio (CPU en unidades ECS, memoria en MiB)"
  type = map(object({
    cpu     = number
    memoria = number
    minimo  = number
    maximo  = number
  }))
  default = {
    core           = { cpu = 512, memoria = 1024, minimo = 2, maximo = 6 }
    "mapa-calor"   = { cpu = 1024, memoria = 2048, minimo = 1, maximo = 4 }
    "estres-malla" = { cpu = 512, memoria = 1024, minimo = 1, maximo = 4 }
  }
}
