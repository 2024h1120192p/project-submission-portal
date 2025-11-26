# Observability Stack Configuration

This directory contains the Kubernetes manifests and configurations for the observability stack including **Prometheus**, **Grafana**, **Loki**, and **Alertmanager**.

## Stack Components

### 1. **Prometheus**
- **Role**: Metrics collection and storage
- **Chart**: kube-prometheus-stack v56.6.0
- **Features**:
  - Automatic service discovery for all microservices
  - Custom scrape configs for application services
  - 7-day retention period
  - 15s scrape interval
  - Prometheus Operator for CRD management

### 2. **Grafana**
- **Role**: Metrics visualization and dashboards
- **Chart**: grafana v7.3.9
- **Features**:
  - Pre-configured Prometheus datasource
  - Pre-configured Loki datasource
  - Application monitoring dashboard
  - Kubernetes cluster dashboard
  - Loki logs dashboard
  - Automatic dashboard provisioning

### 3. **Loki**
- **Role**: Log aggregation and querying
- **Chart**: loki-stack v2.10.2
- **Features**:
  - Promtail for log collection on all nodes
  - Boltdb-shipper for index management
  - Filesystem storage (can be replaced with S3)
  - 10MB/s ingestion rate limit
  - Log retention policies

### 4. **Alertmanager**
- **Role**: Alert routing and notification
- **Features**:
  - Severity-based routing (critical, warning, info)
  - Slack integration (requires webhook URL)
  - Service-based routing
  - Alert inhibition rules
  - Grouped notifications

## Files Overview

| File | Purpose |
|------|---------|
| `namespace.yaml` | Observability namespace definition |
| `prometheus-configmap.yaml` | Prometheus scrape configuration for all services |
| `prometheus-rules.yaml` | Alert rules for applications and infrastructure |
| `loki-config.yaml` | Loki configuration and storage settings |
| `grafana-datasources.yaml` | Data source configuration for Prometheus and Loki |
| `grafana-dashboards.yaml` | Pre-built dashboards (Application, Kubernetes, Logs) |
| `alertmanager-config.yaml` | Alert routing rules and notification channels |
| `servicemonitor.yaml` | Prometheus ServiceMonitor and PodMonitor definitions |
| `rbac.yaml` | Service accounts and RBAC policies |
| `ingress.yaml` | Ingress and LoadBalancer service definitions |
| `kustomization.yaml` | Kustomize configuration for deployment |

## Deployment Instructions

### Prerequisites
- GKE cluster with kube-prometheus-stack and loki-stack already deployed
- kubectl configured with cluster access
- Optional: Slack webhook URL for alerts

### Step 1: Deploy Configuration Manifests

```bash
# Apply all observability configurations
kubectl apply -k k8s/observability/

# Verify deployment
kubectl get all -n observability
kubectl get configmaps -n observability
kubectl get servicemonitors -n observability
```

### Step 2: Configure Alert Notifications (Optional)

Update the Slack webhook URL in `alertmanager-config.yaml`:

```bash
# Edit the alertmanager config
kubectl edit configmap alertmanager-config -n observability

# Replace placeholder with actual webhook URL
slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
```

Reload alertmanager:
```bash
kubectl rollout restart statefulset/alertmanager-kube-prometheus-stack-alertmanager -n observability
```

### Step 3: Access the Dashboards

#### Grafana (Main Dashboard)
```bash
kubectl port-forward svc/grafana 3000:80 -n observability
# Access at http://localhost:3000
# Default credentials: admin/admin (change immediately!)
```

#### Prometheus
```bash
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n observability
# Access at http://localhost:9090
```

#### Alertmanager
```bash
kubectl port-forward svc/kube-prometheus-stack-alertmanager 9093:9093 -n observability
# Access at http://localhost:9093
```

#### Loki
```bash
kubectl port-forward svc/loki-stack 3100:3100 -n observability
# Access at http://localhost:3100
```

### Step 4: Verify Data Collection

1. **Check Prometheus targets**:
   - Go to http://localhost:9090/targets
   - Verify all application services are being scraped

2. **Check Loki logs**:
   - Go to Grafana → Explore → Loki
   - Query: `{job=~".*-service"}`

3. **View Dashboards**:
   - Application Overview: Shows request rates, error rates, latency
   - Kubernetes Cluster: Shows node and pod health
   - Loki Logs: Shows application and system logs

## Configuration Details

### Prometheus Scrape Targets

The configuration automatically discovers and scrapes:
- All microservices in `paper-submission-portal` namespace
- Services labeled with `monitoring: enabled`
- Kubernetes API server
- Node exporters
- Loki metrics
- Prometheus metrics

### Alert Rules

Configured alerts include:

**Application Alerts**:
- High error rate (>5%)
- High latency (p95 > 1s)
- Service unavailability

**Infrastructure Alerts**:
- Node memory/disk pressure
- Pod crash looping
- PersistentVolume filling up

**Platform Alerts**:
- Loki request errors
- Prometheus config reload failures

### Grafana Dashboards

**Application Overview**:
- Request rate across all services
- Error rate (5xx responses)
- Response time (p95 latency)
- Service memory usage

**Kubernetes Cluster**:
- Node count and health
- Pod count and failures
- CPU and memory utilization
- Ready nodes count

**Loki Logs**:
- Real-time log streaming from all services
- Log filtering by job/service

## Customization Guide

### Adding a New Service to Monitoring

1. **Add scrape config** in `prometheus-configmap.yaml`:
```yaml
- job_name: 'new-service'
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
          - paper-submission-portal
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      action: keep
      regex: new-service
    - source_labels: [__meta_kubernetes_pod_port_name]
      action: keep
      regex: metrics
```

2. **Apply the update**:
```bash
kubectl apply -f k8s/observability/prometheus-configmap.yaml
```

3. **Prometheus will auto-reload** configuration changes

### Adding Alert Rules

Edit `prometheus-rules.yaml` and add new rule groups:

```yaml
- alert: MyCustomAlert
  expr: metric_name > threshold
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Alert summary"
    description: "Alert details: {{ $value }}"
```

### Adding Custom Dashboards

1. Create dashboard in Grafana UI
2. Export as JSON
3. Add to `grafana-dashboards.yaml` ConfigMap
4. Apply configuration:
```bash
kubectl apply -f k8s/observability/grafana-dashboards.yaml
kubectl rollout restart deployment/grafana -n observability
```

## Troubleshooting

### Prometheus not scraping targets
```bash
kubectl logs -n observability -l app.kubernetes.io/name=prometheus -c prometheus
```

### Loki not receiving logs
```bash
kubectl logs -n observability -l app=loki-stack-promtail
```

### Grafana datasources not connecting
```bash
kubectl logs -n observability -l app.kubernetes.io/name=grafana
```

### ConfigMap not updating
```bash
# Check ConfigMap
kubectl get configmap prometheus-additional-scrape-configs -n observability -o yaml

# Restart Prometheus to reload config
kubectl rollout restart statefulset/prometheus-kube-prometheus-stack-prometheus -n observability
```

## Production Recommendations

1. **Enable Persistence** for Prometheus and Loki:
   - Update values in Terraform module
   - Use GCP Cloud Storage (GCS) for Loki

2. **Secure Access**:
   - Use authentication proxy (e.g., oauth2-proxy)
   - Enable TLS/HTTPS
   - Restrict ingress sources

3. **Increase Retention**:
   - Prometheus: Update `retention` in prometheus spec
   - Loki: Configure S3 backend with longer retention

4. **Resource Limits**:
   - Set memory/CPU limits
   - Monitor resource usage in Grafana

5. **High Availability**:
   - Deploy multiple replicas
   - Use remote storage (GCS, S3)
   - Configure persistent volumes

## Links and Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [kube-prometheus-stack Helm Chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
