# K3s Learning Guide - IterativeAICouncil E2E Testing

## 🎯 What We're Building

An **ephemeral End-to-End (E2E) testing pipeline** that:
1. Creates AWS infrastructure from scratch
2. Deploys a K3s Kubernetes cluster
3. Builds and pushes a Docker image
4. Deploys our application to K3s
5. Validates everything works
6. Destroys all resources automatically

## 🏗️ Architecture Overview

```
GitHub Actions (CI/CD)
    ↓
Terraform (Infrastructure as Code)
    ↓
AWS EC2 Instance
    ↓
K3s (Lightweight Kubernetes)
    ↓
Docker Container (Our App)
    ↓
NodePort Service (Port 30080)
```

## 📚 Key Concepts

### 1. **K3s - Lightweight Kubernetes**
- **What**: A certified Kubernetes distribution designed for IoT, edge, and CI/CD
- **Why**: Full Kubernetes is heavy (~1GB binary), K3s is ~50MB
- **Perfect for**: Single-node deployments, testing, development
- **Installation**: Single command: `curl -sfL https://get.k3s.io | sh -`

### 2. **Kubernetes Core Concepts**

#### **Nodes**
- Physical or virtual machines that run your workloads
- In our case: 1 EC2 instance = 1 K3s node
- Command: `kubectl get nodes`

#### **Pods**
- Smallest deployable unit in Kubernetes
- Wraps one or more containers
- Has its own IP address
- Command: `kubectl get pods -A` (all namespaces)

#### **Services**
- Exposes pods to network traffic
- Types:
  - **ClusterIP**: Internal only (default)
  - **NodePort**: Exposes on a port on each node (we use this!)
  - **LoadBalancer**: Cloud provider load balancer
- Command: `kubectl get svc -A`

#### **Deployments**
- Manages pod replicas
- Handles rolling updates
- Self-healing (restarts failed pods)
- Command: `kubectl get deployments -A`

### 3. **NodePort Service (Port 30080)**
- **What**: Exposes our app on a specific port on the EC2 instance
- **Why**: Allows external access without a load balancer
- **Port Range**: 30000-32767 (Kubernetes NodePort range)
- **Our Choice**: 30080 (easy to remember, like 8080)
- **Access**: `http://<EC2_IP>:30080`

### 4. **AWS Systems Manager (SSM)**
- **What**: Allows running commands on EC2 without SSH keys
- **Why**: More secure, no key management, works through IAM
- **How**: `aws ssm send-command` → runs command → `get-command-invocation` → gets output
- **Use Case**: Running `kubectl` commands from GitHub Actions

### 5. **user-data.sh - Bootstrap Script**
- **What**: Script that runs when EC2 instance first boots
- **Our Script Does**:
  1. Installs K3s
  2. Configures kubectl
  3. Pulls Docker image from ECR
  4. Applies Kubernetes manifests
  5. Deploys our application

## 🔄 E2E Workflow Stages

### Stage 1: Infrastructure Creation (Terraform)
**What happens:**
- Creates VPC, subnet, internet gateway
- Creates security group (allows ports 22, 80, 443, 6443, 30080)
- Creates ECR repository for Docker images
- Creates IAM role for EC2 to pull from ECR
- Launches EC2 instance with user-data.sh

**Verification:**
- ✅ Terraform outputs exist (EC2 IP, ECR URL, Instance ID)
- ✅ EC2 instance state is "running"
- ✅ ECR repository exists

### Stage 2: Docker Build & Push
**What happens:**
- Builds Docker image from Dockerfile
- Tags with commit SHA and "latest"
- Pushes to ECR repository

**Verification:**
- ✅ Docker build succeeds (exit code 0)
- ✅ Docker push succeeds for both tags
- ✅ Image exists in ECR (describe-images)
- ✅ Image digest is valid

### Stage 3: EC2 Initialization
**What happens:**
- EC2 boots up
- user-data.sh runs automatically
- K3s installs (~2-3 minutes)
- Kubernetes manifests applied
- Pods start

**Verification:**
- ✅ SSH port (22) is accessible
- ✅ cloud-init status shows "done"
- ✅ Wait period completes

### Stage 4: K3s Cluster Verification
**What happens:**
- Use AWS SSM to run kubectl commands
- Check node status
- Check pod status
- Check service status

**Verification:**
- ✅ K3s node is "Ready"
- ✅ AICouncil pod exists
- ✅ AICouncil pod is "Running"
- ✅ NodePort service exists on port 30080

### Stage 5: Application Health Check
**What happens:**
- Poll `/health` endpoint
- Verify application responds
- Check API docs endpoint

**Verification:**
- ✅ Health endpoint returns 200
- ✅ Response contains "status"
- ✅ API docs (/docs) returns 200

### Stage 6: Cleanup
**What happens:**
- Terraform destroy removes all resources
- ECR images remain (for debugging)

**Verification:**
- ✅ All 14 resources destroyed
- ✅ backend.tf restored

## 🎓 Learning Checkpoints in Workflow

Each stage includes:
- **📊 What's happening** - Clear description
- **🔍 Commands being run** - Actual kubectl/aws commands
- **✅ Verification** - How we know it worked
- **🎓 Learning notes** - Why this matters

## 🛠️ Useful Commands

### On EC2 Instance (via SSH or SSM)
```bash
# Check K3s status
sudo systemctl status k3s

# View K3s logs
sudo journalctl -u k3s -f

# Check nodes
sudo kubectl get nodes -o wide

# Check all pods
sudo kubectl get pods -A

# Check specific pod logs
sudo kubectl logs -n default <pod-name>

# Check services
sudo kubectl get svc -A

# Describe a pod (detailed info)
sudo kubectl describe pod <pod-name>

# Get pod YAML
sudo kubectl get pod <pod-name> -o yaml
```

### From GitHub Actions (via SSM)
```bash
# Run any command on EC2
aws ssm send-command \
  --instance-ids <instance-id> \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["<your-command>"]'

# Get command output
aws ssm get-command-invocation \
  --command-id <command-id> \
  --instance-id <instance-id>
```

## 📖 Further Reading

- [K3s Documentation](https://docs.k3s.io/)
- [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [AWS SSM Documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/what-is-systems-manager.html)


