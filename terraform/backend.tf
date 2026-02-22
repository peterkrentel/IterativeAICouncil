terraform {
  backend "s3" {
    # Backend config is provided via -backend-config flags in GitHub Actions
    # or via backend-config.tfvars file created by bootstrap.sh
  }

  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

