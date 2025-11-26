#!/bin/bash

# Deploy Observability Stack Configuration
# This script applies all observability configurations to the Kubernetes cluster

set -e

NAMESPACE="observability"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📊 Deploying Observability Stack Configuration..."
echo "=================================================="

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: Cannot access Kubernetes cluster"
    exit 1
fi

# Check if namespace exists
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "✓ Namespace '$NAMESPACE' already exists"
else
    echo "✓ Creating namespace '$NAMESPACE'..."
    kubectl create namespace "$NAMESPACE"
fi

# Apply kustomization
echo ""
echo "📝 Applying Kubernetes manifests..."
kubectl apply -k "$SCRIPT_DIR/"

# Wait for deployments to be ready
echo ""
echo "⏳ Waiting for observability stack to be ready..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/grafana -n "$NAMESPACE" 2>/dev/null || \
    echo "⚠️  Note: Grafana deployment status check skipped"

kubectl wait --for=condition=ready --timeout=300s \
    pod -l app.kubernetes.io/name=prometheus -n "$NAMESPACE" 2>/dev/null || \
    echo "⚠️  Note: Prometheus pod status check skipped"

# Apply ingress configuration
echo ""
echo "🌐 Applying ingress and load balancer configuration..."
kubectl apply -f "$SCRIPT_DIR/ingress.yaml"

echo ""
echo "✅ Observability stack configuration deployed successfully!"
echo ""
echo "📊 Next steps:"
echo "=================================================="
echo ""
echo "1. Access Grafana:"
echo "   kubectl port-forward svc/grafana 3000:80 -n $NAMESPACE"
echo "   Then visit: http://localhost:3000 (admin/admin)"
echo ""
echo "2. Access Prometheus:"
echo "   kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n $NAMESPACE"
echo "   Then visit: http://localhost:9090"
echo ""
echo "3. Access Alertmanager:"
echo "   kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n $NAMESPACE"
echo "   Then visit: http://localhost:9093"
echo ""
echo "4. Access Loki:"
echo "   kubectl port-forward svc/loki-stack 3100:3100 -n $NAMESPACE"
echo "   Then visit: http://localhost:3100"
echo ""
echo "5. Configure Slack alerts (if needed):"
echo "   kubectl edit configmap alertmanager-config -n $NAMESPACE"
echo ""
echo "📈 Check deployment status:"
echo "   kubectl get all -n $NAMESPACE"
echo "   kubectl get configmaps -n $NAMESPACE"
echo "   kubectl get servicemonitors -n $NAMESPACE"
echo ""
echo "📖 See README.md for detailed configuration guide"
