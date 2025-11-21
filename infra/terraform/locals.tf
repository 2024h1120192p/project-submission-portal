#=============================================================================
# LOCAL VALUES
#=============================================================================

locals {
  # Common resource naming
  resource_prefix = "${var.environment}-${var.gcp_project_id}"

  # Common tags to apply to all resources
  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "paper-submission-portal"
  }

  # GCP labels (lowercase and dash-separated as per GCP requirements)
  gcp_labels = {
    environment = var.environment
    managed-by  = "terraform"
    project     = "paper-submission-portal"
  }

  # AWS tags (can use mixed case and underscores)
  aws_tags = merge(
    local.common_tags,
    {
      Application = "PaperSubmissionPortal"
    }
  )

  # Naming patterns
  gke_cluster_name = "${var.environment}-core-gke"
  cloudsql_name    = "${var.environment}-pg"
  msk_cluster_name = "${var.environment}-msk"
  emr_cluster_name = "${var.environment}-emr-flink"
  lambda_name      = "${var.environment}-pdf-extract"

  # Database names
  database_names = {
    users       = "users"
    submissions = "submissions"
  }

  # Computed values
  enable_emr_deployment = var.flink_job_jar != ""

  # Kubernetes namespaces
  k8s_namespaces = {
    default       = "default"
    observability = "observability"
    argocd        = "argocd"
  }
}
