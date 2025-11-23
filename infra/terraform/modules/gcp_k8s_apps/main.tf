variable "namespace" {}
variable "gateway_host" {
  description = "Domain for gateway ingress (use empty string to accept any host)"
  type        = string
  default     = ""
}

# Ingress for gateway service
# Supports both domain-based and IP-based access
resource "kubernetes_ingress_v1" "gateway" {
  metadata {
    name      = "gateway-ingress"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/ingress.class"                 = "gce"
      "kubernetes.io/ingress.allow-http"            = "true"
      "kubernetes.io/ingress.global-static-ip-name" = "" # Optional: reserve static IP
    }
  }
  spec {
    # Default backend for any host (works with IP or domain)
    default_backend {
      service {
        name = "gateway"
        port {
          number = 80
        }
      }
    }

    # Optional: host-based routing if domain is specified
    dynamic "rule" {
      for_each = var.gateway_host != "" ? [1] : []
      content {
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
