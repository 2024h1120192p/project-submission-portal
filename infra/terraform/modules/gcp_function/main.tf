variable "project_id" {}
variable "region" {}
variable "bucket_name" {}
variable "function_name" {}
variable "source_dir" {}

# NOTE: Simplified placeholder for a 2nd gen Cloud Function built from Cloud Run container image or source.
# In practice you'll package source with gcloud or use Cloud Build. This is a scaffold only.
resource "google_cloudfunctions2_function" "pdf_extract" {
  name     = var.function_name
  location = var.region
  project  = var.project_id
  build_config {
    runtime     = "python312"
    entry_point = "handler" # Adjust to actual function entry
    source {
      storage_source {
        bucket = var.bucket_name
        object = "function-source.zip" # Upload manually or via CI
      }
    }
  }
  service_config {
    max_instance_count = 3
    available_memory   = "512M"
    timeout_seconds    = 60
  }
}

# Event trigger (placeholder) - you need to create a trigger for GCS finalize events via google_eventarc_trigger or cloudfunction triggers.
# TODO: Add google_eventarc_trigger for bucket object finalize to invoke function.

output "name" { value = google_cloudfunctions2_function.pdf_extract.name }
