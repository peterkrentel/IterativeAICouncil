output "ec2_public_ip" {
  description = "Public IP of EC2 instance"
  value       = aws_instance.k3s.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.k3s.id
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.aicouncil.repository_url
}

output "ssh_private_key" {
  description = "SSH private key (sensitive)"
  value       = var.ssh_public_key != "" ? "Using provided key" : tls_private_key.k3s.private_key_pem
  sensitive   = true
}

output "ssh_command" {
  description = "SSH command to connect to EC2"
  value       = "ssh -i k3s-key.pem ubuntu@${aws_instance.k3s.public_ip}"
}

output "kubeconfig_command" {
  description = "Command to get kubeconfig"
  value       = "scp -i k3s-key.pem ubuntu@${aws_instance.k3s.public_ip}:~/.kube/config ./kubeconfig"
}

