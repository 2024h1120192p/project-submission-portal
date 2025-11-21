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

