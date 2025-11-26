#!/bin/bash

# Observability Stack Health Check Script
# Verifies all components are deployed and functioning correctly

set -e

NAMESPACE="observability"
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     Observability Stack Health Check                       ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check resource existence
check_resource() {
    local resource_type=$1
    local resource_name=$2
    
    if kubectl get "$resource_type" "$resource_name" -n "$NAMESPACE" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $resource_type: $resource_name"
        return 0
    else
        echo -e "${RED}✗${NC} $resource_type: $resource_name (NOT FOUND)"
        return 1
    fi
}

# Function to check pod status
check_pod_status() {
    local pod_label=$1
    local expected_ready=$2
    
    local ready=$(kubectl get pods -n "$NAMESPACE" -l "$pod_label" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)
    
    if [ "$ready" -ge "$expected_ready" ]; then
        echo -e "${GREEN}✓${NC} Pods with label '$pod_label': $ready ready"
        return 0
    else
        echo -e "${RED}✗${NC} Pods with label '$pod_label': $ready ready (expected $expected_ready)"
        return 1
    fi
}

# Check Namespace
echo -e "${BOLD}Checking Namespace...${NC}"
kubectl get namespace "$NAMESPACE" &> /dev/null && echo -e "${GREEN}✓${NC} Namespace '$NAMESPACE' exists" || echo -e "${RED}✗${NC} Namespace not found"
echo ""

# Check Deployments
echo -e "${BOLD}Checking Deployments...${NC}"
check_pod_status "app.kubernetes.io/name=prometheus" 1 || true
check_pod_status "app.kubernetes.io/name=grafana" 1 || true
check_pod_status "app.kubernetes.io/name=loki" 1 || true
check_pod_status "app.kubernetes.io/name=alertmanager" 1 || true
echo ""

# Check StatefulSets
echo -e "${BOLD}Checking StatefulSets...${NC}"
kubectl get statefulsets -n "$NAMESPACE" &> /dev/null && \
    echo -e "${GREEN}✓${NC} StatefulSets: $(kubectl get statefulsets -n "$NAMESPACE" --no-headers | wc -l) found" || \
    echo -e "${RED}✗${NC} No StatefulSets found"
echo ""

# Check ConfigMaps
echo -e "${BOLD}Checking Configuration...${NC}"
configs=(
    "prometheus-additional-scrape-configs"
    "grafana-datasources"
    "grafana-dashboards-config"
    "loki-config"
    "alertmanager-config"
)
config_found=0
for config in "${configs[@]}"; do
    if kubectl get configmap "$config" -n "$NAMESPACE" &> /dev/null; then
        echo -e "${GREEN}✓${NC} ConfigMap: $config"
        ((config_found++))
    else
        echo -e "${YELLOW}⚠${NC} ConfigMap: $config (not found)"
    fi
done
echo "  Total: $config_found/${#configs[@]} configurations found"
echo ""

# Check ServiceMonitors
echo -e "${BOLD}Checking Service Monitors...${NC}"
monitors=(
    "application-services"
    "loki-monitor"
    "prometheus-monitor"
)
monitors_found=0
for monitor in "${monitors[@]}"; do
    if kubectl get servicemonitor "$monitor" -n "$NAMESPACE" &> /dev/null; then
        echo -e "${GREEN}✓${NC} ServiceMonitor: $monitor"
        ((monitors_found++))
    else
        echo -e "${YELLOW}⚠${NC} ServiceMonitor: $monitor (not found)"
    fi
done
echo "  Total: $monitors_found/${#monitors[@]} service monitors found"
echo ""

# Check PrometheusRules
echo -e "${BOLD}Checking Alert Rules...${NC}"
if kubectl get prometheusrule "application-alerts" -n "$NAMESPACE" &> /dev/null; then
    rule_count=$(kubectl get prometheusrule "application-alerts" -n "$NAMESPACE" -o jsonpath='{.spec.groups[*].rules}' | jq 'length' 2>/dev/null || echo "?")
    echo -e "${GREEN}✓${NC} PrometheusRule: application-alerts ($rule_count rules)"
else
    echo -e "${YELLOW}⚠${NC} PrometheusRule: application-alerts (not found)"
fi
echo ""

# Check Services
echo -e "${BOLD}Checking Services...${NC}"
services=(
    "grafana"
    "kube-prometheus-stack-prometheus"
    "kube-prometheus-stack-alertmanager"
    "loki-stack"
)
services_found=0
for service in "${services[@]}"; do
    if kubectl get service "$service" -n "$NAMESPACE" &> /dev/null; then
        echo -e "${GREEN}✓${NC} Service: $service"
        ((services_found++))
    else
        echo -e "${RED}✗${NC} Service: $service (not found)"
    fi
done
echo "  Total: $services_found/${#services[@]} core services found"
echo ""

# Check LoadBalancer Services
echo -e "${BOLD}Checking LoadBalancer Services...${NC}"
lbs=(
    "grafana-lb"
    "prometheus-lb"
    "alertmanager-lb"
    "loki-lb"
)
lbs_found=0
for lb in "${lbs[@]}"; do
    if kubectl get service "$lb" -n "$NAMESPACE" &> /dev/null; then
        external_ip=$(kubectl get service "$lb" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
        echo -e "${GREEN}✓${NC} LoadBalancer: $lb ($external_ip)"
        ((lbs_found++))
    else
        echo -e "${YELLOW}⚠${NC} LoadBalancer: $lb (not found)"
    fi
done
echo "  Total: $lbs_found/${#lbs[@]} load balancer services found"
echo ""

# Check Ingress
echo -e "${BOLD}Checking Ingress...${NC}"
if kubectl get ingress -n "$NAMESPACE" &> /dev/null; then
    ingress_count=$(kubectl get ingress -n "$NAMESPACE" --no-headers | wc -l)
    echo -e "${GREEN}✓${NC} Ingress: $ingress_count ingress rules configured"
else
    echo -e "${YELLOW}⚠${NC} No ingress found"
fi
echo ""

# Check RBAC
echo -e "${BOLD}Checking RBAC...${NC}"
rbac_items=(
    "serviceaccount/observability-admin"
    "clusterrole/observability-admin"
    "clusterrolebinding/observability-admin"
)
rbac_found=0
for rbac in "${rbac_items[@]}"; do
    if kubectl get "$rbac" -n "$NAMESPACE" &> /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} RBAC: $rbac"
        ((rbac_found++))
    else
        echo -e "${YELLOW}⚠${NC} RBAC: $rbac (not found)"
    fi
done
echo "  Total: $rbac_found/${#rbac_items[@]} RBAC items found"
echo ""

# Check Pod Status
echo -e "${BOLD}Checking Pod Status...${NC}"
pod_count=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l)
total_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | wc -l)
echo -e "${GREEN}✓${NC} Pods Running: $pod_count/$total_pods"

# Check for any failing pods
failing_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l || echo "0")
if [ "$failing_pods" -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} Failing Pods: $failing_pods"
    kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running --no-headers | head -5
else
    echo -e "${GREEN}✓${NC} No failing pods"
fi
echo ""

# Summary
echo -e "${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║ Health Check Summary                                       ║${NC}"
echo -e "${BOLD}╠════════════════════════════════════════════════════════════╣${NC}"

total_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | wc -l)
running_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l)
ready_deployments=$(kubectl get deployments -n "$NAMESPACE" --no-headers 2>/dev/null | grep "1/1" | wc -l || echo "0")
ready_statefulsets=$(kubectl get statefulsets -n "$NAMESPACE" --no-headers 2>/dev/null | grep "1/1" | wc -l || echo "0")

echo -e "${BOLD}│${NC} Total Pods: $total_pods | Running: $running_pods"
echo -e "${BOLD}│${NC} Deployments Ready: $ready_deployments"
echo -e "${BOLD}│${NC} StatefulSets Ready: $ready_statefulsets"
echo -e "${BOLD}│${NC} Configurations: $config_found"
echo -e "${BOLD}│${NC} Service Monitors: $monitors_found"
echo -e "${BOLD}│${NC} Services: $services_found"
echo -e "${BOLD}│${NC} LoadBalancers: $lbs_found"

if [ "$running_pods" -eq "$total_pods" ] && [ "$config_found" -ge 4 ]; then
    echo -e "${BOLD}│${NC}"
    echo -e "${BOLD}│${NC} ${GREEN}✓ Status: ALL SYSTEMS OPERATIONAL${NC}"
else
    echo -e "${BOLD}│${NC}"
    echo -e "${BOLD}│${NC} ${YELLOW}⚠ Status: PARTIAL (some components may still be initializing)${NC}"
fi

echo -e "${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Print access information
echo -e "${BOLD}Access Information:${NC}"
echo ""
echo "Grafana (Admin/Admin):"
grafana_lb=$(kubectl get service grafana-lb -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
[ "$grafana_lb" != "pending" ] && echo "  http://$grafana_lb" || echo "  http://localhost:3000 (port-forward: kubectl port-forward svc/grafana 3000:80 -n $NAMESPACE)"

echo ""
echo "Prometheus:"
prom_lb=$(kubectl get service prometheus-lb -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
[ "$prom_lb" != "pending" ] && echo "  http://$prom_lb:9090" || echo "  http://localhost:9090 (port-forward: kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n $NAMESPACE)"

echo ""
echo "Alertmanager:"
alert_lb=$(kubectl get service alertmanager-lb -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
[ "$alert_lb" != "pending" ] && echo "  http://$alert_lb:9093" || echo "  http://localhost:9093 (port-forward: kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n $NAMESPACE)"

echo ""
echo "Loki:"
loki_lb=$(kubectl get service loki-lb -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
[ "$loki_lb" != "pending" ] && echo "  http://$loki_lb:3100" || echo "  http://localhost:3100 (port-forward: kubectl port-forward svc/loki-stack 3100:3100 -n $NAMESPACE)"

echo ""
echo -e "${BOLD}Documentation:${NC}"
echo "  README.md         - Comprehensive configuration guide"
echo "  QUICKSTART.md     - Quick access and operations"
echo "  DEPLOYMENT_SUMMARY.md - Deployment details"
echo ""
