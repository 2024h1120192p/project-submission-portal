# Kubernetes Deployment Guide

## Overview

This project uses Kubernetes for container orchestration. The configuration is organized as follows:

## Directory Structure

```
Project/
├── services/                    # Service code with Dockerfiles
│   ├── users_service/
│   │   ├── Dockerfile          # Dockerfile for users service
│   │   └── app/
│   ├── gateway/
│   │   ├── Dockerfile
│   │   └── app/
│   ├── analytics_service/
│   │   ├── Dockerfile
│   │   └── app/
│   ├── notification_service/
│   │   ├── Dockerfile
│   │   └── app/
│   ├── plagiarism_service/
│   │   ├── Dockerfile
│   │   └── app/
│   └── submission_service/
│       ├── Dockerfile
│       └── app/
├── k8s/                        # Kubernetes configurations
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   └── secrets.yaml
│   ├── users-service/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── gateway/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   └── ... (other services)
├── libs/                       # Shared libraries
├── build-images.sh             # Script to build all Docker images
└── deploy-k8s.sh               # Script to deploy to Kubernetes
```

## Building Docker Images

Each service has its own Dockerfile in its service directory. The Dockerfiles are designed to:
1. Copy the entire monorepo (including shared `libs/`)
2. Install dependencies
3. Run the specific service

### Build All Images

```bash
# Build all images with default registry and tag
./build-images.sh

# Build with custom registry and tag
REGISTRY=myregistry.io TAG=v1.0.0 ./build-images.sh
```

### Build Individual Image

```bash
# Build from project root (important for monorepo context)
docker build -f services/users_service/Dockerfile -t h20240192/ss_g527.paper-submission-portal/users-service:latest .
```

### Push Images to Registry

```bash
# Push all images
for service in users_service gateway analytics_service notification_service plagiarism_service submission_service; do
  docker push h20240192/ss_g527.paper-submission-portal/$service:latest
done
```

## Kubernetes Deployment

### Prerequisites

1. A running Kubernetes cluster (minikube, GKE, EKS, AKS, etc.)
2. `kubectl` configured to access your cluster
3. Container images pushed to a registry accessible by your cluster

### Configuration Steps

1. **Update Image Registry**: Edit all `k8s/*/deployment.yaml` files and replace `h20240192/ss_g527.paper-submission-portal` with your actual container registry.

2. **Update Secrets**: Edit `k8s/base/secrets.yaml` and add your base64-encoded secrets:
   ```bash
   echo -n "your-secret-value" | base64
   ```

3. **Update Ingress Domain**: Edit `k8s/gateway/ingress.yaml` and set your domain name.

### Deploy to Kubernetes

```bash
# Deploy everything
./deploy-k8s.sh

# Or deploy manually step-by-step
kubectl apply -f k8s/base/
kubectl apply -f k8s/users-service/
kubectl apply -f k8s/gateway/
kubectl apply -f k8s/analytics-service/
kubectl apply -f k8s/notification-service/
kubectl apply -f k8s/plagiarism-service/
kubectl apply -f k8s/submission-service/
```

### Verify Deployment

```bash
# Check all resources
kubectl get all -n project-submission-portal

# Check pods
kubectl get pods -n project-submission-portal

# Check services
kubectl get services -n project-submission-portal

# View logs
kubectl logs -f deployment/gateway -n project-submission-portal
```

### Access the Application

For **LoadBalancer** service type:
```bash
kubectl get service gateway -n project-submission-portal
# Access via the EXTERNAL-IP shown
```

For **NodePort** (local development):
```bash
kubectl get service gateway -n project-submission-portal
# Access via http://<node-ip>:<node-port>
```

For **Ingress**:
- Configure DNS to point your domain to the ingress controller's IP
- Access via http://your-domain.com

## Local Development with Minikube

```bash
# Start minikube
minikube start

# Enable ingress addon
minikube addons enable ingress

# Build images directly in minikube (skip push step)
eval $(minikube docker-env)
./build-images.sh

# Deploy
./deploy-k8s.sh

# Get service URL
minikube service gateway -n project-submission-portal
```

## Updating Services

```bash
# 1. Rebuild the image
docker build -f services/users_service/Dockerfile -t h20240192/ss_g527.paper-submission-portal/users-service:v2 .

# 2. Push to registry
docker push h20240192/ss_g527.paper-submission-portal/users-service:v2

# 3. Update deployment
kubectl set image deployment/users-service users-service=h20240192/ss_g527.paper-submission-portal/users-service:v2 -n project-submission-portal

# Or update the YAML and reapply
kubectl apply -f k8s/users-service/deployment.yaml
```

## Scaling Services

```bash
# Scale a specific service
kubectl scale deployment users-service --replicas=5 -n project-submission-portal

# Or edit the deployment.yaml and reapply
```

## Debugging

```bash
# Get pod logs
kubectl logs <pod-name> -n project-submission-portal

# Follow logs
kubectl logs -f deployment/users-service -n project-submission-portal

# Execute commands in pod
kubectl exec -it <pod-name> -n project-submission-portal -- /bin/bash

# Describe pod for events
kubectl describe pod <pod-name> -n project-submission-portal

# Port forward for local testing
kubectl port-forward service/users-service 8001:8001 -n project-submission-portal
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace project-submission-portal

# Or delete individual components
kubectl delete -f k8s/users-service/
kubectl delete -f k8s/gateway/
# ... etc
```

## Important Notes

1. **Build Context**: Always build Docker images from the project root directory to include shared `libs/` and `config/`.

2. **Image Registry**: Update all deployment YAML files with your actual registry before deploying.

3. **Secrets Management**: Never commit actual secrets to version control. Use Kubernetes secrets or external secret managers.

4. **Health Checks**: Add `/health` endpoints to your services for liveness and readiness probes.

5. **Resource Limits**: Adjust CPU and memory limits in deployment YAMLs based on your needs.

## CI/CD Integration

Example GitHub Actions workflow structure:

```yaml
name: Build and Deploy
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build images
        run: ./build-images.sh
      - name: Push images
        run: |
          # Push logic here
      - name: Deploy to K8s
        run: ./deploy-k8s.sh
```
