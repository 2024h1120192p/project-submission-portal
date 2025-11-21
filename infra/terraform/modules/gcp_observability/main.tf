variable "namespace" {}

resource "kubernetes_namespace" "obs" {
  metadata { name = var.namespace }
}

# Prometheus stack (kube-prometheus-stack) includes Prometheus + Alertmanager + node exporters
resource "helm_release" "prometheus_stack" {
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.obs.metadata[0].name
  version    = "56.6.0"
  values = [<<EOF
prometheus:
  prometheusSpec:
    retention: 7d
    scrapeInterval: 15s
EOF
  ]
}

# Grafana
resource "helm_release" "grafana" {
  name       = "grafana"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana"
  namespace  = kubernetes_namespace.obs.metadata[0].name
  version    = "7.3.9"
  values = [<<EOF
ingress:
  enabled: false
EOF
  ]
}

# Loki stack for logs
resource "helm_release" "loki" {
  name       = "loki-stack"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki-stack"
  namespace  = kubernetes_namespace.obs.metadata[0].name
  version    = "2.10.2"
  values = [<<EOF
loki:
  persistence:
    enabled: false
EOF
  ]
}
