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
