#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y curl wget git

# Install AWS CLI for ECR authentication
apt-get install -y awscli

# Install ECR credential helper (needed for K3s/containerd to pull from ECR)
echo "Installing ECR credential helper..."
wget https://amazon-ecr-credential-helper-releases.s3.us-east-2.amazonaws.com/0.7.1/linux-amd64/docker-credential-ecr-login
chmod +x docker-credential-ecr-login
mv docker-credential-ecr-login /usr/local/bin/

# Configure K3s/containerd to use ECR credential helper
# This MUST be done BEFORE K3s is installed so containerd picks up the config
echo "Configuring K3s/containerd for ECR authentication..."
mkdir -p /etc/rancher/k3s
cat > /etc/rancher/k3s/registries.yaml <<EOF
configs:
  "${ecr_registry}":
    auth:
      username: AWS
      password_command: "/usr/local/bin/docker-credential-ecr-login get"
EOF

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

# Create kubeconfig for remote access
mkdir -p /home/ubuntu/.kube
cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
chown -R ubuntu:ubuntu /home/ubuntu/.kube

# Deploy application manifests
echo "Deploying application..."

# Create namespace and secrets
kubectl create secret generic aicouncil-secrets \
  --from-literal=GROQ_API_KEY="" \
  --from-literal=GOOGLE_API_KEY="" \
  --dry-run=client -o yaml | kubectl apply -f -

# Create deployment
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aicouncil
  labels:
    app: aicouncil
spec:
  replicas: 1
  selector:
    matchLabels:
      app: aicouncil
  template:
    metadata:
      labels:
        app: aicouncil
    spec:
      containers:
      - name: aicouncil
        image: ${ecr_registry}:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: aicouncil-secrets
              key: GROQ_API_KEY
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: aicouncil-secrets
              key: GOOGLE_API_KEY
        - name: PORT
          value: "8000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: aicouncil
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 8000
    nodePort: 30080
    protocol: TCP
    name: http
  selector:
    app: aicouncil
EOF

echo "K3s installation and deployment complete!"

