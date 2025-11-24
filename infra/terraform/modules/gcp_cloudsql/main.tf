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
  default     = true
}

#=============================================================================
# CLOUD SQL MODULE - RESOURCES
#=============================================================================

resource "google_sql_database_instance" "pg" {
  name                = var.instance_name
  database_version    = var.engine_version
  region              = var.region
  project             = var.project_id
  deletion_protection = false

  settings {
    tier = var.tier
    ip_configuration {
      ipv4_enabled = var.ipv4_enabled
    }
    availability_type = var.availability_type
  }
}

resource "google_sql_database" "users" {
  name     = var.users_db_name
  instance = google_sql_database_instance.pg.name
  project  = var.project_id
}

resource "google_sql_database" "submissions" {
  name     = var.submissions_db_name
  instance = google_sql_database_instance.pg.name
  project  = var.project_id
}

#=============================================================================
# CLOUD SQL MODULE - OUTPUTS
#=============================================================================

output "connection_name" {
  description = "Cloud SQL instance connection name (project:region:instance)"
  value       = google_sql_database_instance.pg.connection_name
}

output "instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.pg.name
}

output "users_database_name" {
  description = "Name of the users database"
  value       = google_sql_database.users.name
}

output "submissions_database_name" {
  description = "Name of the submissions database"
  value       = google_sql_database.submissions.name
}

output "self_link" {
  description = "Self link to the Cloud SQL instance"
  value       = google_sql_database_instance.pg.self_link
}

