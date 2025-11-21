variable "namespace" {}
variable "chart_version" {}

resource "kubernetes_namespace" "argocd" {
  metadata { name = var.namespace }
}

resource "helm_release" "argo" {
  name       = "argo-cd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  namespace  = kubernetes_namespace.argocd.metadata[0].name
  version    = var.chart_version
  values = [<<EOF
server:
  service:
    type: ClusterIP
  ingress:
    enabled: false
EOF
  ]
}

output "namespace" { value = kubernetes_namespace.argocd.metadata[0].name }
