#=============================================================================
# GKE MODULE - OUTPUTS
#=============================================================================

output "name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "endpoint" {
  description = "GKE cluster endpoint (API server URL)"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "ca_certificate" {
  description = "Base64 encoded cluster CA certificate"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "location" {
  description = "GKE cluster location (region or zone)"
  value       = google_container_cluster.primary.location
}

output "cluster_id" {
  description = "GKE cluster unique identifier"
  value       = google_container_cluster.primary.id
}
