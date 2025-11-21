resource "google_sql_database_instance" "pg" {
  name             = var.instance_name
  database_version = var.engine_version
  region           = var.region
  project          = var.project_id

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

