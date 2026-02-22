variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro" # Free tier eligible for first 12 months
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "aicouncil"
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
  default     = "" # Will be generated if not provided
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed to SSH to EC2"
  type        = list(string)
  default     = ["0.0.0.0/0"] # WARNING: Open to world. Restrict in production!
}

