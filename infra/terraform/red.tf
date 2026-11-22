# ── VPC en 2 zonas de disponibilidad ─────────────────────────────────
# públicas : ALB y NAT Gateway
# privadas : tareas ECS (sin IP pública)
# datos    : RDS (sin ruta a internet)

resource "aws_vpc" "principal" {
  cidr_block           = var.cidr_vpc
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = { Name = local.nombre }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.principal.id
  tags   = { Name = local.nombre }
}

resource "aws_subnet" "publica" {
  count                   = 2
  vpc_id                  = aws_vpc.principal.id
  availability_zone       = local.azs[count.index]
  cidr_block              = cidrsubnet(var.cidr_vpc, 8, count.index)
  map_public_ip_on_launch = false
  tags                    = { Name = "${local.nombre}-publica-${count.index}" }
}

resource "aws_subnet" "privada" {
  count             = 2
  vpc_id            = aws_vpc.principal.id
  availability_zone = local.azs[count.index]
  cidr_block        = cidrsubnet(var.cidr_vpc, 8, 10 + count.index)
  tags              = { Name = "${local.nombre}-privada-${count.index}" }
}

resource "aws_subnet" "datos" {
  count             = 2
  vpc_id            = aws_vpc.principal.id
  availability_zone = local.azs[count.index]
  cidr_block        = cidrsubnet(var.cidr_vpc, 8, 20 + count.index)
  tags              = { Name = "${local.nombre}-datos-${count.index}" }
}

resource "aws_eip" "nat" {
  count  = var.nat_unico ? 1 : 2
  domain = "vpc"
  tags   = { Name = "${local.nombre}-nat-${count.index}" }
}

resource "aws_nat_gateway" "nat" {
  count         = var.nat_unico ? 1 : 2
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.publica[count.index].id
  tags          = { Name = "${local.nombre}-nat-${count.index}" }
  depends_on    = [aws_internet_gateway.igw]
}

resource "aws_route_table" "publica" {
  vpc_id = aws_vpc.principal.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "${local.nombre}-publica" }
}

resource "aws_route_table_association" "publica" {
  count          = 2
  subnet_id      = aws_subnet.publica[count.index].id
  route_table_id = aws_route_table.publica.id
}

resource "aws_route_table" "privada" {
  count  = 2
  vpc_id = aws_vpc.principal.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat[var.nat_unico ? 0 : count.index].id
  }
  tags = { Name = "${local.nombre}-privada-${count.index}" }
}

resource "aws_route_table_association" "privada" {
  count          = 2
  subnet_id      = aws_subnet.privada[count.index].id
  route_table_id = aws_route_table.privada[count.index].id
}

# Endpoint de S3 (gateway, sin costo): el tráfico a S3 no pasa por el NAT.
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.principal.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.privada[*].id
  tags              = { Name = "${local.nombre}-s3" }
}

# ── Grupos de seguridad ──────────────────────────────────────────────
data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

resource "aws_security_group" "alb" {
  name        = "${local.nombre}-alb"
  description = "ALB: solo acepta trafico desde CloudFront"
  vpc_id      = aws_vpc.principal.id

  ingress {
    description     = "HTTPS desde los nodos de CloudFront"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    prefix_list_ids = [data.aws_ec2_managed_prefix_list.cloudfront.id]
  }
  ingress {
    description     = "HTTP desde CloudFront (redirigido a HTTPS)"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    prefix_list_ids = [data.aws_ec2_managed_prefix_list.cloudfront.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.cidr_vpc]
  }
}

resource "aws_security_group" "servicios" {
  name        = "${local.nombre}-servicios"
  description = "Tareas ECS: solo reciben trafico del ALB"
  vpc_id      = aws_vpc.principal.id

  ingress {
    description     = "Puerto de la aplicacion desde el ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  egress {
    description = "Salida a internet via NAT (SES, ECR, Secrets Manager) y a RDS"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name        = "${local.nombre}-rds"
  description = "PostgreSQL: solo desde las tareas ECS"
  vpc_id      = aws_vpc.principal.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.servicios.id]
  }
}
