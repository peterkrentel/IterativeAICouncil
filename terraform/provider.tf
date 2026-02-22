provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "AICouncil"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

