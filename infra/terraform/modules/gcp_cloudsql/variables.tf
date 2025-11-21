#=============================================================================
# CLOUD SQL MODULE - VARIABLES
#=============================================================================

variable "project_id" {
  description = "GCP project ID where Cloud SQL instance will be created"
  type        = string
}

variable "region" {
  description = "GCP region for the Cloud SQL instance"
  type        = string
}

variable "tier" {
  description = "Machine tier for Cloud SQL instance (e.g., db-f1-micro, db-custom-1-3840)"
  type        = string
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
}

variable "instance_name" {
  description = "Name of the Cloud SQL instance"
  type        = string
}

variable "users_db_name" {
  description = "Name of the users database"
  type        = string
}

variable "submissions_db_name" {
  description = "Name of the submissions database"
  type        = string
}

variable "availability_type" {
  description = "Availability type (ZONAL or REGIONAL)"
  type        = string
  default     = "ZONAL"
}

variable "ipv4_enabled" {
  description = "Whether to enable IPv4 (public IP) for the instance"
  type        = bool
  default     = false
}
