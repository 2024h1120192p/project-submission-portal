#=============================================================================
# GKE MODULE - VARIABLES
#=============================================================================

variable "project_id" {
  description = "GCP project ID where GKE cluster will be created"
  type        = string
}

variable "region" {
  description = "GCP region for the GKE cluster"
  type        = string
}

variable "zones" {
  description = "List of zones for multi-zone node pool distribution"
  type        = list(string)
}

variable "cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
}

variable "network_name" {
  description = "VPC network name (null for default network)"
  type        = string
  default     = null
}

variable "subnetwork_name" {
  description = "Subnetwork name (null for default subnetwork)"
  type        = string
  default     = null
}

variable "node_count" {
  description = "Number of nodes per zone in the default node pool"
  type        = number
  default     = 2
}

variable "machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-4"
}

variable "environment" {
  description = "Environment label for nodes"
  type        = string
  default     = "dev"
}

#=============================================================================
# GKE MODULE - RESOURCES
#=============================================================================

resource "google_container_cluster" "primary" {
  name                     = var.cluster_name
  location                 = var.region
  project                  = var.project_id
  remove_default_node_pool = true
  initial_node_count       = 1

  networking_mode = "VPC_NATIVE"
  release_channel { channel = "REGULAR" }

  workload_identity_config { workload_pool = "${var.project_id}.svc.id.goog" }

  ip_allocation_policy {}
}

resource "google_container_node_pool" "default" {
  name       = "default-pool"
  project    = var.project_id
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count

  node_config {
    machine_type = var.machine_type
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    labels       = { environment = var.environment }
  }
}

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

