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
