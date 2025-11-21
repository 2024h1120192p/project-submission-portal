variable "namespace" {}
variable "gateway_host" {}

# Ingress placeholder for gateway service
resource "kubernetes_ingress_v1" "gateway" {
  metadata {
    name      = "gateway-ingress"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/ingress.class" = "gce" # Adjust for ingress controller used
    }
  }
  spec {
    rule {
      host = var.gateway_host
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = "gateway"
              port { number = 80 }
            }
          }
        }
      }
    }
  }
}

# HPAs for multiple services (gateway, users, submissions, notification, plagiarism)
locals {
  hpa_services = ["gateway", "users", "submissions", "notification", "plagiarism"]
}

resource "kubernetes_horizontal_pod_autoscaler_v2" "hpas" {
  for_each = toset(local.hpa_services)
  metadata {
    name      = "${each.key}-hpa"
    namespace = var.namespace
  }
  spec {
    scale_target_ref {
      kind        = "Deployment"
      name        = each.key
      api_version = "apps/v1"
    }
    min_replicas = 2
    max_replicas = 6
    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = 70
        }
      }
    }
  }
}
