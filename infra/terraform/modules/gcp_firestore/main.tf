variable "project_id" {}
variable "database_id" {}

resource "google_firestore_database" "db" {
  project     = var.project_id
  name        = var.database_id
  location_id = "us-central"
  type        = "FIRESTORE_NATIVE"
}

output "database_id" { value = google_firestore_database.db.name }
