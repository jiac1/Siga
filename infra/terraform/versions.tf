terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Estado remoto: crear el bucket y la tabla una vez (ver infra/README.md) y
  # completar con -backend-config=backend.hcl en `terraform init`.
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = local.etiquetas
  }
}

# CloudFront exige certificados ACM en us-east-1.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  default_tags {
    tags = local.etiquetas
  }
}
