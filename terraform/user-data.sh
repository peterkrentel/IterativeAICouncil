#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y curl wget git

# Install AWS CLI for ECR authentication
apt-get install -y awscli

# Install K3s
echo "Installing K3s..."
curl -sfL https://get.k3s.io | sh -s - \
  --write-kubeconfig-mode 644 \
  --disable traefik \
  --node-name k3s-master

# Wait for K3s to be ready
echo "Waiting for K3s to be ready..."
until kubectl get nodes | grep -q "Ready"; do
  sleep 5
done

# Install Traefik as ingress controller
echo "Installing Traefik..."
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v2.10/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v2.10/docs/content/reference/dynamic-configuration/kubernetes-crd-rbac.yml

# Create Traefik deployment
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: traefik-ingress-controller
  namespace: default
---
kind: Deployment
apiVersion: apps/v1
metadata:
  name: traefik
  namespace: default
  labels:
    app: traefik
spec:
  replicas: 1
  selector:
    matchLabels:
      app: traefik
  template:
    metadata:
      labels:
        app: traefik
    spec:
      serviceAccountName: traefik-ingress-controller
      containers:
        - name: traefik
          image: traefik:v2.10
          args:
            - --api.insecure=true
            - --providers.kubernetesingress
            - --entrypoints.web.address=:80
          ports:
            - name: web
              containerPort: 80
            - name: admin
              containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: traefik
  namespace: default
spec:
  type: NodePort
  ports:
    - protocol: TCP
      name: web
      port: 80
      nodePort: 30080
    - protocol: TCP
      name: admin
      port: 8080
      nodePort: 30808
  selector:
    app: traefik
EOF

# Configure ECR authentication helper
echo "Configuring ECR authentication..."
mkdir -p /root/.docker
cat > /root/.docker/config.json <<EOF
{
  "credsStore": "ecr-login"
}
EOF

# Install ECR credential helper
wget https://amazon-ecr-credential-helper-releases.s3.us-east-2.amazonaws.com/0.7.1/linux-amd64/docker-credential-ecr-login
chmod +x docker-credential-ecr-login
mv docker-credential-ecr-login /usr/local/bin/

# Create kubeconfig for remote access
mkdir -p /home/ubuntu/.kube
cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
chown -R ubuntu:ubuntu /home/ubuntu/.kube

echo "K3s installation complete!"

