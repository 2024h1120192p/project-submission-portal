#!/bin/bash

# Deploy script for Kubernetes
# This script applies all Kubernetes configurations

set -e

echo "Deploying to Kubernetes..."

# Apply base configurations
echo "Applying base configurations..."
echo "Creating namespace..."
kubectl apply -f k8s/base/namespace.yaml
kubectl wait --for=condition=Active --timeout=30s namespace/paper-submission-portal

echo "Applying secrets and configmaps..."
kubectl apply -f k8s/base/secrets.yaml
kubectl apply -f k8s/base/configmap.yaml

# Apply all service configurations
echo "Applying service configurations..."
kubectl apply -f k8s/users-service/
kubectl apply -f k8s/gateway/
kubectl apply -f k8s/analytics-service/
kubectl apply -f k8s/notification-service/
kubectl apply -f k8s/plagiarism-service/
kubectl apply -f k8s/submission-service/

echo ""
echo "========================================="
echo "Deployment complete!"
echo "========================================="
echo ""
echo "Check status with:"
echo "  kubectl get pods -n paper-submission-portal"
echo "  kubectl get services -n paper-submission-portal"
echo ""
echo "View logs with:"
echo "  kubectl logs -f deployment/<service-name> -n paper-submission-portal"
