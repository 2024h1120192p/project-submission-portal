variable "project_id" {}
variable "database_id" {}

# Manage existing Firestore database
# The database already exists in GCP, so we import it rather than create it
resource "google_firestore_database" "db" {
  project     = var.project_id
  name        = var.database_id
  location_id = "us-central1"
  type        = "FIRESTORE_NATIVE"
  
  # Prevent accidental deletion of the database
  lifecycle {
    prevent_destroy = true
    # Ignore changes to prevent recreation attempts
    ignore_changes = [
      location_id,
      type,
    ]
  }
}

output "database_id" { value = google_firestore_database.db.name }
